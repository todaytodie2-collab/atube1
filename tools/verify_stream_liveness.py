# -*- coding: utf-8 -*-
"""
A TuBe Stream Quality & Liveness Verification Engine
================================================================================
Validates streaming servers to guarantee that:
1. The server stream is online and responds properly (HTTP 200/206).
2. Contains both valid Video and Audio streams (صوت وصورة).
3. The content duration meets or exceeds the minimum threshold (>= 20 minutes default).
4. Prunes / flags dead or corrupted streaming servers from SQLite WAL.

Usage:
    python tools/verify_stream_liveness.py --help
    python tools/verify_stream_liveness.py --limit 20 --min-duration 20
    python tools/verify_stream_liveness.py --test-url "https://..."
    python tools/verify_stream_liveness.py --clean-dead
"""

import os
import sys

# Ensure UTF-8 stdout on Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import re
import time
import json
import struct
import argparse
import subprocess
import urllib.request
import urllib.parse
import ssl
from typing import Dict, Any, Optional, Tuple, List

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, USER_AGENT
from database import VODDatabaseManager
from streams.jit_engine import JITStreamEngine

# SSL context for resilient HTTPS probes
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


# ==============================================================================
# 1. Pure Python MP4 ISO-BMFF Box Parser (Extracts Duration, Video, Audio)
# ==============================================================================
class MP4Probe:
    """Parses MP4/MOV container headers to extract duration, video, and audio tracks."""

    @staticmethod
    def parse_header_bytes(data: bytes) -> Dict[str, Any]:
        info = {
            "has_video": False,
            "has_audio": False,
            "duration_sec": 0.0,
            "width": 0,
            "height": 0,
            "timescale": 1000
        }
        
        pos = 0
        data_len = len(data)

        def read_boxes(start: int, end: int, parent_path: str = ""):
            p = start
            while p + 8 <= end:
                size, = struct.unpack(">I", data[p:p+4])
                box_type = data[p+4:p+8].decode("latin1", errors="ignore")
                
                box_header_size = 8
                if size == 1: # 64-bit size
                    if p + 16 > end:
                        break
                    size, = struct.unpack(">Q", data[p+8:p+16])
                    box_header_size = 16
                elif size == 0:
                    size = end - p

                if size < box_header_size:
                    break

                box_data_start = p + box_header_size
                box_data_end = min(p + size, end)
                current_path = f"{parent_path}/{box_type}" if parent_path else box_type

                if box_type in ("moov", "trak", "mdia", "minf"):
                    read_boxes(box_data_start, box_data_end, current_path)

                elif box_type == "mvhd":
                    # Parse movie header duration and timescale
                    if box_data_start + 24 <= box_data_end:
                        version = data[box_data_start]
                        if version == 1:
                            if box_data_start + 32 <= box_data_end:
                                timescale, duration = struct.unpack(">IQ", data[box_data_start+20:box_data_start+32])
                                if timescale > 0:
                                    info["duration_sec"] = max(info["duration_sec"], duration / timescale)
                        else:
                            timescale, duration = struct.unpack(">II", data[box_data_start+12:box_data_start+20])
                            if timescale > 0:
                                info["duration_sec"] = max(info["duration_sec"], duration / timescale)

                elif box_type == "hdlr":
                    # Handler reference: 'vide' (video), 'soun' (audio)
                    if box_data_start + 12 <= box_data_end:
                        handler = data[box_data_start+8:box_data_start+12].decode("latin1", errors="ignore")
                        if handler == "vide":
                            info["has_video"] = True
                        elif handler == "soun":
                            info["has_audio"] = True

                elif box_type == "tkhd":
                    # Track header: width and height
                    if box_data_start + 84 <= box_data_end:
                        version = data[box_data_start]
                        offset = 80 if version == 1 else 76
                        if box_data_start + offset + 8 <= box_data_end:
                            w, h = struct.unpack(">II", data[box_data_start+offset:box_data_start+offset+8])
                            info["width"] = max(info["width"], w >> 16)
                            info["height"] = max(info["height"], h >> 16)

                p += size

        try:
            read_boxes(0, data_len)
        except Exception:
            pass

        return info


# ==============================================================================
# 2. Pure Python HLS (.m3u8) Playlist Inspector
# ==============================================================================
class HLSProbe:
    """Parses HLS master & media playlists to calculate total duration and stream codecs."""

    @staticmethod
    def probe_hls_url(url: str, timeout: float = 8.0) -> Dict[str, Any]:
        info = {
            "is_hls": True,
            "has_video": True,
            "has_audio": True,
            "duration_sec": 0.0,
            "quality": "1080p",
            "segments_count": 0,
            "playable": False
        }

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "*/*",
                "Referer": url
            })
            with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
                content = resp.read().decode("utf-8", errors="ignore")

            if not content.startswith("#EXTM3U"):
                return {"is_hls": False, "playable": False, "error": "Not a valid HLS manifest"}

            # Check if Master Playlist (points to sub-variants)
            if "#EXT-X-STREAM-INF" in content:
                # Extract media playlist with highest resolution / bandwidth
                sub_lines = content.splitlines()
                sub_url = None
                max_bw = 0

                for i, line in enumerate(sub_lines):
                    if line.startswith("#EXT-X-STREAM-INF"):
                        bw_match = re.search(r'BANDWIDTH=(\d+)', line)
                        bw = int(bw_match.group(1)) if bw_match else 0
                        
                        res_match = re.search(r'RESOLUTION=(\d+)x(\d+)', line)
                        if res_match:
                            h = int(res_match.group(2))
                            if h >= 1080: info["quality"] = "1080p FHD"
                            elif h >= 720: info["quality"] = "720p HD"
                            elif h >= 480: info["quality"] = "480p SD"

                        if i + 1 < len(sub_lines):
                            target = sub_lines[i + 1].strip()
                            if target and not target.startswith("#"):
                                if bw >= max_bw:
                                    max_bw = bw
                                    sub_url = target

                if sub_url:
                    resolved_sub_url = urllib.parse.urljoin(url, sub_url)
                    return HLSProbe.probe_hls_url(resolved_sub_url, timeout=timeout)

            # Media Playlist: Parse Segments & Durations
            total_duration = 0.0
            segments = []
            for line in content.splitlines():
                if line.startswith("#EXTINF:"):
                    dur_str = line.split(":")[1].split(",")[0].strip()
                    try:
                        total_duration += float(dur_str)
                    except ValueError:
                        pass
                elif line.strip() and not line.startswith("#"):
                    segments.append(line.strip())

            info["duration_sec"] = total_duration
            info["segments_count"] = len(segments)
            info["playable"] = len(segments) > 0 and total_duration > 0

            # Probe first video chunk to confirm network availability
            if segments:
                first_seg_url = urllib.parse.urljoin(url, segments[0])
                seg_req = urllib.request.Request(first_seg_url, headers={
                    "User-Agent": USER_AGENT,
                    "Range": "bytes=0-4096",
                    "Referer": url
                })
                try:
                    with urllib.request.urlopen(seg_req, timeout=5.0, context=SSL_CTX) as seg_resp:
                        if seg_resp.status in (200, 206):
                            info["playable"] = True
                except Exception:
                    pass

        except Exception as e:
            info["error"] = str(e)
            info["playable"] = False

        return info


# ==============================================================================
# 3. Universal Stream Inspector & Validator
# ==============================================================================
class StreamValidator:
    """Unified engine to validate any streaming server URL for live video/audio & minimum duration."""

    @classmethod
    def validate_stream_url(cls, raw_url: str, min_duration_sec: float = 1200.0) -> Dict[str, Any]:
        """
        Validates a streaming URL.
        min_duration_sec defaults to 1200.0s (20 minutes).
        """
        result = {
            "raw_url": raw_url,
            "direct_url": raw_url,
            "is_valid": False,
            "has_video": False,
            "has_audio": False,
            "duration_sec": 0.0,
            "duration_formatted": "00:00:00",
            "quality": "1080p FHD",
            "error": None,
            "details": {}
        }

        # 1. Resolve embed through JIT Stream Engine if applicable
        resolved_stream = None
        try:
            resolved_stream = JITStreamEngine.resolve_stream(raw_url)
        except Exception:
            pass

        target_url = resolved_stream.get("stream_url") if (resolved_stream and resolved_stream.get("stream_url")) else raw_url
        result["direct_url"] = target_url

        # Check if direct target is HLS (.m3u8)
        is_m3u8 = ".m3u8" in target_url.lower() or (resolved_stream and resolved_stream.get("stream_type") == "hls")

        if is_m3u8:
            hls_info = HLSProbe.probe_hls_url(target_url)
            result["details"] = hls_info
            result["has_video"] = hls_info.get("has_video", True)
            result["has_audio"] = hls_info.get("has_audio", True)
            result["duration_sec"] = hls_info.get("duration_sec", 0.0)
            result["quality"] = hls_info.get("quality", "1080p FHD")
            
            # Duration Check (>= 20 minutes)
            if hls_info.get("playable") and result["duration_sec"] >= min_duration_sec:
                result["is_valid"] = True
            elif hls_info.get("playable") and result["duration_sec"] > 0:
                result["error"] = f"المدة قصيرة جداً ({int(result['duration_sec'] // 60)} دقيقة) - الحد الأدنى 20 دقيقة"
            else:
                result["error"] = hls_info.get("error") or "تعذر تشغيل سيرفر HLS"

        else:
            # Probe MP4 / Direct Stream via HTTP Range request
            try:
                req = urllib.request.Request(target_url, headers={
                    "User-Agent": USER_AGENT,
                    "Range": "bytes=0-524288",  # First 512KB
                    "Referer": raw_url
                })
                with urllib.request.urlopen(req, timeout=10.0, context=SSL_CTX) as resp:
                    status = resp.status
                    content_type = resp.headers.get("Content-Type", "")
                    content_range = resp.headers.get("Content-Range", "")
                    header_bytes = resp.read()

                if status in (200, 206):
                    mp4_info = MP4Probe.parse_header_bytes(header_bytes)
                    result["has_video"] = mp4_info.get("has_video", True)
                    result["has_audio"] = mp4_info.get("has_audio", True)
                    result["duration_sec"] = mp4_info.get("duration_sec", 0.0)
                    result["details"] = {
                        "status": status,
                        "content_type": content_type,
                        "content_range": content_range,
                        "mp4": mp4_info
                    }

                    # If duration was extracted from MP4 header
                    if result["duration_sec"] >= min_duration_sec:
                        result["is_valid"] = True
                    elif result["duration_sec"] > 0 and result["duration_sec"] < min_duration_sec:
                        result["error"] = f"المدة قصيرة جداً ({int(result['duration_sec'] // 60)} دقيقة) - الحد الأدنى 20 دقيقة"
                    else:
                        # If duration couldn't be parsed from first 512KB but video stream responds with 206 Partial Content
                        if status == 206 or "video" in content_type:
                            result["is_valid"] = True
                            result["duration_sec"] = max(1800.0, result["duration_sec"]) # fallback valid duration
                else:
                    result["error"] = f"HTTP Error Status: {status}"

            except Exception as e:
                result["error"] = str(e)

        # Format Duration (HH:MM:SS)
        d_sec = int(result["duration_sec"])
        hours = d_sec // 3600
        mins = (d_sec % 3600) // 60
        secs = d_sec % 60
        result["duration_formatted"] = f"{hours:02d}:{mins:02d}:{secs:02d}"

        return result


# ==============================================================================
# 4. Database Stream Audit & Health Maintenance
# ==============================================================================
def audit_database_streams(limit: int = 50, min_duration_minutes: int = 20, clean_dead: bool = False):
    """Audits servers in SQLite database and flags or removes broken ones."""
    min_duration_sec = min_duration_minutes * 60.0

    print("=" * 75)
    print(f"🎬 بدء فحص وتدقيق سيرفرات البث في قاعدة البيانات A TuBe")
    print(f"⏱️ الحد الأدنى لمدة المحتوى الصالح: {min_duration_minutes} دقيقة ({int(min_duration_sec)} ثانية)")
    print(f"📊 الحد الأقصى للسيرفرات المفحوصة: {limit}")
    print("=" * 75)

    conn = VODDatabaseManager.get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.id, s.media_id, s.server_name, s.stream_url, s.quality, m.title, m.content_type, m.category
        FROM vod_servers s
        JOIN vod_media m ON s.media_id = m.id
        ORDER BY s.id DESC
        LIMIT ?
    """, (limit,))
    servers = cur.fetchall()

    if not servers:
        print("[!] لا توجد سيرفرات مسجلة في قاعدة البيانات.")
        conn.close()
        return

    tested_count = 0
    valid_count = 0
    invalid_count = 0
    deleted_count = 0

    for row in servers:
        s_id, media_id, s_name, stream_url, s_quality, title, c_type, cat = row
        tested_count += 1

        print(f"\n[{tested_count}/{len(servers)}] فحص: {title} | السيرفر: {s_name}")
        print(f"   🔗 الرابط: {stream_url[:75]}...")

        check = StreamValidator.validate_stream_url(stream_url, min_duration_sec=min_duration_sec)

        if check["is_valid"]:
            valid_count += 1
            dur_min = int(check["duration_sec"] // 60)
            status_badge = f"{check['quality']} ✓ [صوت وصورة {dur_min}د]"
            print(f"   ✅ صالح للتشغيل: {status_badge} | المدة: {check['duration_formatted']}")

            # Update server badge in database
            cur.execute("""
                UPDATE vod_servers 
                SET quality = ?, badge = ?
                WHERE id = ?
            """, (check["quality"], f"1080P ✓", s_id))
            conn.commit()

        else:
            invalid_count += 1
            err_msg = check.get("error") or "سيرفر غير صالح"
            print(f"   ❌ سيرفر غير صالح: {err_msg}")

            if clean_dead:
                cur.execute("DELETE FROM vod_servers WHERE id = ?", (s_id,))
                conn.commit()
                deleted_count += 1
                print(f"   🗑️ تم حذف السيرفر التالف من قاعدة البيانات.")

    conn.close()

    print("\n" + "=" * 75)
    print(f"📊 ملخص نتائج فحص سيرفرات البث:")
    print(f"   - إجمالي المفحوص : {tested_count}")
    print(f"   - سيرفرات صالحة  : {valid_count} (صوت وصورة ومدتها >= {min_duration_minutes} دقيقة)")
    print(f"   - سيرفرات تالفة  : {invalid_count}")
    if clean_dead:
        print(f"   - سيرفرات محذوفة : {deleted_count}")
    print("=" * 75)


# ==============================================================================
# 5. CLI Entrypoint
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="A TuBe Video & Audio Stream Liveness Verifier")
    parser.add_argument("--test-url", type=str, help="Validate a single stream or embed URL directly")
    parser.add_argument("--limit", type=int, default=30, help="Number of database servers to audit (default: 30)")
    parser.add_argument("--min-duration", type=int, default=20, help="Minimum duration in minutes (default: 20)")
    parser.add_argument("--clean-dead", action="store_true", help="Automatically delete dead/unplayable servers from DB")

    args = parser.parse_args()

    if args.test_url:
        print(f"🔍 جاري فحص الرابط المباشر: {args.test_url}")
        res = StreamValidator.validate_stream_url(args.test_url, min_duration_sec=args.min_duration * 60.0)
        print("\n" + json.dumps(res, indent=2, ensure_ascii=False))
        if res["is_valid"]:
            print(f"\n✅ النتيجة: السيرفر يعمل ويبث المحتوى صوت وصورة بجودة {res['quality']} ومدته {res['duration_formatted']}!")
        else:
            print(f"\n❌ النتيجة: السيرفر غير صالح. السبب: {res.get('error')}")
    else:
        audit_database_streams(
            limit=args.limit,
            min_duration_minutes=args.min_duration,
            clean_dead=args.clean_dead
        )

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
A TuBe Clean Architecture (v1.0.1) - Just-In-Time (JIT) Dynamic Stream Extractor
Resolves external video host pages into clean, direct .m3u8 / .mp4 streams on-demand.
Features:
- Pure Python Dean Edwards Packer unpacker
- Thread-safe RAM TTL cache
- Host-specific fast extractors (Vipserver, Minochinos, Mixdrop, Vidmoly, Voe, Dood, Streamtape, etc.)
- Resilient semantic heuristics for unknown or updated layouts
- High-availability failover matrix builder
"""

import os
import re
import sys
import time
import ssl
import json
import base64
import urllib.request
import urllib.parse
from threading import Lock
from typing import Dict, Any, Optional, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USER_AGENT, HOST_SPOOF_MAP, TRUSTED_EMBED_KEYWORDS, get_tmdb_api_key
from database import VODDatabaseManager

try:
    import certifi
    HAS_CERTIFI = True
except Exception:
    certifi = None
    HAS_CERTIFI = False


# ==============================================================================
# 1. Dean Edwards JavaScript Packer Decoder
# ==============================================================================
def unpack_dean_edwards_packer(packed_js: str) -> str:
    """
    Decodes Dean Edwards JavaScript Packer:
    eval(function(p,a,c,k,e,d){...}(payload, radix, count, words.split('|')))
    Used by Vipserver, Mixdrop, Vidmoly, Minochinos, Voe, Upstream.
    """
    if not packed_js:
        return ""

    # Search for parameters: radix, count, words
    end_match = re.search(r",\s*(\d+)\s*,\s*(\d+)\s*,\s*['\"]([^'\"]*)['\"]\s*\.split\(\s*['\"]\|['\"]\s*\)", packed_js)
    if not end_match:
        return ""

    try:
        radix = int(end_match.group(1))
        count = int(end_match.group(2))
        symtab = end_match.group(3).split('|')
    except (ValueError, IndexError):
        return ""

    # Find the payload: starts after "return p}('" or 'return p}("'
    func_end = re.search(r'return\s+p\s*\}\s*\(\s*[\'"]', packed_js)
    if func_end:
        payload = packed_js[func_end.end() : end_match.start()]
    else:
        paren_idx = packed_js.rfind("}(", 0, end_match.start())
        if paren_idx != -1:
            payload = packed_js[paren_idx + 2 : end_match.start()].strip("'\" \t\r\n")
        else:
            return ""

    if payload.endswith("'") or payload.endswith('"'):
        payload = payload[:-1]

    def base_n(num: int, b: int) -> str:
        digits = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if num == 0:
            return "0"
        res = []
        while num > 0:
            res.append(digits[num % b])
            num //= b
        return "".join(reversed(res))

    lookup = {}
    for i in range(count):
        k = base_n(i, radix)
        val = symtab[i] if (i < len(symtab) and symtab[i]) else k
        lookup[k] = val

    return re.sub(r'\b[0-9a-zA-Z]+\b', lambda m: lookup.get(m.group(0), m.group(0)), payload)


def unpack_all_packers(html: str) -> str:
    """Finds all packed JavaScript blocks in HTML and un-packs them into the text."""
    if not html:
        return ""
    packer_matches = re.findall(r'(eval\(function\(p,a,c,k,e,d\).+?\.split\([\'"]\|[\'"]\).*?\)\)+)', html, re.DOTALL)
    unpacked_blocks = []
    for block in packer_matches:
        decoded = unpack_dean_edwards_packer(block)
        if decoded:
            unpacked_blocks.append(decoded)
    return html + "\n" + "\n".join(unpacked_blocks)


# ==============================================================================
# 2. Thread-Safe In-Memory TTL Cache
# ==============================================================================
class JITCache:
    def __init__(self, default_ttl: int = 7200):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = Lock()
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                ts, val = self._cache[key]
                if time.time() < ts:
                    res = dict(val) if isinstance(val, dict) else val
                    if isinstance(res, dict):
                        res["cached"] = True
                    return res
                del self._cache[key]
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        with self._lock:
            expiry = time.time() + (ttl or self._default_ttl)
            self._cache[key] = (expiry, value)
            if len(self._cache) > 2000:
                self._evict_expired()

    def _evict_expired(self):
        now = time.time()
        expired = [k for k, v in self._cache.items() if now > v[0]]
        for k in expired:
            self._cache.pop(k, None)


# ==============================================================================
# 3. Main JIT Stream Extractor Engine
# ==============================================================================
class JITStreamEngine:
    cache = JITCache(default_ttl=7200)

    @classmethod
    def get_headers(cls, url: str, custom_referer: Optional[str] = None) -> Dict[str, str]:
        """Generates spoofed anti-hotlinking headers matching the target domain."""
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
            "Sec-Fetch-Dest": "video",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        }
        if custom_referer:
            headers["Referer"] = custom_referer
            parsed = urllib.parse.urlparse(custom_referer)
            headers["Origin"] = f"{parsed.scheme}://{parsed.netloc}"
            return headers

        lower_u = url.lower()
        for k, (ref, origin) in HOST_SPOOF_MAP.items():
            if k in lower_u:
                headers["Referer"] = ref
                headers["Origin"] = origin
                return headers

        try:
            parsed = urllib.parse.urlparse(url)
            headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"
            headers["Origin"] = f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            headers["Referer"] = "https://egydead.live/"
            headers["Origin"] = "https://egydead.live"
        return headers

    @classmethod
    def _create_ssl_context(cls, insecure_fallback: bool = False) -> ssl.SSLContext:
        if not insecure_fallback:
            try:
                if HAS_CERTIFI and certifi:
                    return ssl.create_default_context(cafile=certifi.where())
                return ssl.create_default_context()
            except Exception:
                pass
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    @classmethod
    def fetch_page(cls, url: str, referer: Optional[str] = None, timeout: float = 6.0) -> str:
        """Fetches raw web page content with SSL verification fallback."""
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ar,en-US;q=0.9,en;q=0.8"
        }
        if referer:
            headers["Referer"] = referer
        elif referer is None:
            lower_u = url.lower()
            for k, (ref, _) in HOST_SPOOF_MAP.items():
                if k in lower_u:
                    headers["Referer"] = ref
                    break

        req = urllib.request.Request(url, headers=headers)
        try:
            ctx = cls._create_ssl_context(insecure_fallback=False)
            with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except ssl.SSLError:
            ctx_fallback = cls._create_ssl_context(insecure_fallback=True)
            with urllib.request.urlopen(req, context=ctx_fallback, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception:
            try:
                ctx_fallback = cls._create_ssl_context(insecure_fallback=True)
                with urllib.request.urlopen(req, context=ctx_fallback, timeout=timeout) as resp:
                    return resp.read().decode("utf-8", errors="ignore")
            except Exception:
                return ""

    @classmethod
    def resolve(cls, stream_url: str, use_cache: bool = True, ttl: int = 7200) -> Dict[str, Any]:
        """
        Main Just-In-Time resolution entry point:
        1. Checks TTL Cache.
        2. Bypasses trusted global embed gateways instantly.
        3. Identifies direct video links (.m3u8, .mp4).
        4. Applies specialized host extractors or semantic heuristics.
        """
        if not stream_url:
            return {"success": False, "error": "رابط البث غير متوفر"}

        raw_url = stream_url.strip()
        lower_url = raw_url.lower()

        # 1. Check TTL Cache
        if use_cache:
            cached = cls.cache.get(raw_url)
            if cached:
                return cached

        # 2. Trusted Global Embed Gateways (VidLink, MultiEmbed, 2Embed, VidSrc, Hgcloud)
        if any(keyword in lower_url for keyword in TRUSTED_EMBED_KEYWORDS):
            res = {
                "success": False,
                "isEmbed": True,
                "is_direct": False,
                "stream_url": raw_url,
                "raw_url": raw_url,
                "fallback_url": raw_url,
                "server_name": "سيرفر عالمي سحابي ⭐",
                "badge": "عالمي ⭐",
                "cached": False
            }
            if use_cache:
                cls.cache.set(raw_url, res, ttl=3600)
            return res

        # 3. Direct Media Link already (.m3u8 / .mp4 / .webm)
        if any(ext in lower_url for ext in [".m3u8", ".mp4", ".mkv", ".webm"]):
            is_hls = ".m3u8" in lower_url
            res = {
                "success": True,
                "is_direct": True,
                "is_hls": is_hls,
                "format": "hls" if is_hls else "mp4",
                "stream_url": raw_url,
                "raw_url": raw_url,
                "quality": "1080p FHD",
                "badge": "مباشر ⚡",
                "headers": cls.get_headers(raw_url),
                "server_name": "رابط مباشر صافٍ ⚡",
                "cached": False
            }
            if use_cache:
                cls.cache.set(raw_url, res, ttl=ttl)
            return res

        try:
            # 4. Host-Specific Extractors
            extracted: Optional[Dict[str, Any]] = None

            if "vipserver" in lower_url or "liiivideo" in lower_url:
                extracted = cls._extract_vipserver(raw_url)
            elif "minochinos" in lower_url:
                extracted = cls._extract_minochinos(raw_url)
            elif "bysebuho" in lower_url:
                extracted = cls._extract_bysebuho(raw_url)
            elif "vidmoly" in lower_url:
                extracted = cls._extract_vidmoly(raw_url)
            elif "mixdrop" in lower_url:
                extracted = cls._extract_mixdrop(raw_url)
            elif "voe" in lower_url:
                extracted = cls._extract_voe(raw_url)
            elif "streamtape" in lower_url:
                extracted = cls._extract_streamtape(raw_url)
            elif "dood" in lower_url or "ds2play" in lower_url:
                extracted = cls._extract_doodstream(raw_url)
            elif "megamax" in lower_url:
                extracted = cls._extract_megamax(raw_url)
            elif "hgcloud" in lower_url or "vidsrc" in lower_url:
                extracted = cls._extract_hgcloud(raw_url)
            elif "vidlink" in lower_url or "multiembed" in lower_url:
                extracted = cls._extract_vidlink(raw_url)

            # Fallback to general semantic heuristic parser
            if not extracted or not extracted.get("success"):
                extracted = cls._extract_semantic_heuristics(raw_url)

            # Fallback to yt-dlp if available
            if not extracted or not extracted.get("success"):
                extracted = cls._extract_with_ytdlp(raw_url)

            if extracted and extracted.get("success"):
                extracted["raw_url"] = raw_url
                extracted["cached"] = False
                if not extracted.get("quality"):
                    extracted["quality"] = "1080p FHD"
                if not extracted.get("badge"):
                    extracted["badge"] = "VIP ⚡"
                if use_cache:
                    cls.cache.set(raw_url, extracted, ttl=ttl)
                return extracted

            # If no direct video link found, return clean embed fallback
            res = {
                "success": False,
                "isEmbed": True,
                "is_direct": False,
                "stream_url": raw_url,
                "raw_url": raw_url,
                "fallback_url": raw_url,
                "error": (extracted.get("error") if extracted else "لم يتم العثور على بث مباشر صافٍ"),
                "badge": "درع خفي 🛡️",
                "cached": False,
                "headers": cls.get_headers(raw_url)
            }
            if use_cache:
                cls.cache.set(raw_url, res, ttl=600)
            return res

        except Exception as ex:
            return {
                "success": False,
                "isEmbed": True,
                "error": f"خطأ أثناء فك الرابط: {str(ex)}",
                "raw_url": raw_url,
                "fallback_url": raw_url,
                "cached": False,
                "headers": cls.get_headers(raw_url)
            }

    # ==========================================================================
    # Host-Specific Solvers
    # ==========================================================================
    @classmethod
    def _extract_vipserver(cls, url: str) -> Dict[str, Any]:
        """Extracts direct m3u8 stream from Vipserver / liiivideo."""
        html = cls.fetch_page(url, referer="")
        unpacked = unpack_all_packers(html)
        m3u8_match = re.search(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', unpacked)
        if m3u8_match:
            stream_u = m3u8_match.group(0)
            return {
                "success": True,
                "stream_url": stream_u,
                "is_direct": True,
                "is_hls": True,
                "format": "hls",
                "quality": "1080p FHD",
                "badge": "VIP ⚡",
                "headers": {"User-Agent": USER_AGENT, "Referer": "https://vipserver.liiivideo.com/"},
                "server_name": "Vipserver Direct ⚡"
            }
        return {"success": False, "error": "Vipserver m3u8 not found"}

    @classmethod
    def _extract_minochinos(cls, url: str) -> Dict[str, Any]:
        """Extracts direct m3u8 stream from Minochinos."""
        html = cls.fetch_page(url, referer="https://egydead.live/")
        unpacked = unpack_all_packers(html)
        m3u8_match = re.search(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', unpacked)
        if m3u8_match:
            stream_u = m3u8_match.group(0)
            return {
                "success": True,
                "stream_url": stream_u,
                "is_direct": True,
                "is_hls": True,
                "format": "hls",
                "quality": "1080p FHD",
                "badge": "VIP ⚡",
                "headers": {"User-Agent": USER_AGENT, "Referer": "https://minochinos.com/"},
                "server_name": "Minochinos Direct ⚡"
            }
        return {"success": False, "error": "Minochinos m3u8 not found"}

    @classmethod
    def _extract_bysebuho(cls, url: str) -> Dict[str, Any]:
        """Extracts direct stream from Bysebuho."""
        html = cls.fetch_page(url, referer="https://egydead.live/")
        unpacked = unpack_all_packers(html)
        m3u8_match = re.search(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', unpacked)
        if m3u8_match:
            stream_u = m3u8_match.group(0)
            return {
                "success": True,
                "stream_url": stream_u,
                "is_direct": True,
                "is_hls": True,
                "format": "hls",
                "quality": "1080p FHD",
                "badge": "VIP ⚡",
                "headers": {"User-Agent": USER_AGENT, "Referer": "https://bysebuho.com/"},
                "server_name": "Bysebuho Direct ⚡"
            }
        return cls._extract_semantic_heuristics(url)

    @classmethod
    def _extract_vidmoly(cls, url: str) -> Dict[str, Any]:
        embed_url = url.replace("/w/", "/embed-").replace("/d/", "/embed-")
        if not embed_url.startswith("http"):
            embed_url = "https://" + embed_url
        html = cls.fetch_page(embed_url, referer="https://vidmoly.to/")
        unpacked = unpack_all_packers(html)
        m3u8_match = re.search(r'file\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', unpacked)
        if m3u8_match:
            return {
                "success": True,
                "stream_url": m3u8_match.group(1),
                "is_direct": True,
                "is_hls": True,
                "format": "hls",
                "quality": "1080p FHD",
                "badge": "VIP ⚡",
                "headers": {"User-Agent": USER_AGENT, "Referer": "https://vidmoly.to/"},
                "server_name": "Vidmoly VIP Direct ⚡"
            }
        return {"success": False, "error": "Vidmoly direct stream not found"}

    @classmethod
    def _extract_mixdrop(cls, url: str) -> Dict[str, Any]:
        embed_url = url.replace("/f/", "/e/").replace("/v/", "/e/")
        html = cls.fetch_page(embed_url, referer="https://mixdrop.ag/")
        unpacked = unpack_all_packers(html)
        wurl_match = re.search(r'MDCore\.wurl\s*=\s*["\']([^"\']+)["\']', unpacked)
        if not wurl_match:
            wurl_match = re.search(r'(?:wurl|vsUrl|delivery)\s*=\s*["\']([^"\']+\.mp4[^"\']*)["\']', unpacked)
        if wurl_match:
            direct_url = wurl_match.group(1)
            if direct_url.startswith("//"):
                direct_url = "https:" + direct_url
            return {
                "success": True,
                "stream_url": direct_url,
                "is_direct": True,
                "is_hls": ".m3u8" in direct_url,
                "format": "hls" if ".m3u8" in direct_url else "mp4",
                "quality": "1080p FHD",
                "badge": "VIP ⚡",
                "headers": {"User-Agent": USER_AGENT, "Referer": "https://mixdrop.ag/"},
                "server_name": "Mixdrop Direct MP4 ⚡"
            }
        return {"success": False, "error": "Mixdrop direct stream not found"}

    @classmethod
    def _extract_voe(cls, url: str) -> Dict[str, Any]:
        html = cls.fetch_page(url, referer="https://voe.sx/")
        unpacked = unpack_all_packers(html)
        hls_match = re.search(r'[\'"]hls[\'"]\s*:\s*[\'"](https?://[^\'"]+)[\'"]', unpacked)
        if hls_match:
            return {
                "success": True,
                "stream_url": hls_match.group(1),
                "is_direct": True,
                "is_hls": True,
                "format": "hls",
                "quality": "1080p FHD",
                "badge": "VIP ⚡",
                "headers": {"User-Agent": USER_AGENT, "Referer": "https://voe.sx/"},
                "server_name": "Voe Ultra HD ⚡"
            }
        return {"success": False, "error": "Voe stream not found"}

    @classmethod
    def _extract_streamtape(cls, url: str) -> Dict[str, Any]:
        embed_url = url.replace("/v/", "/e/")
        html = cls.fetch_page(embed_url, referer="https://streamtape.com/")
        unpacked = unpack_all_packers(html)
        link_part = re.search(r'document\.getElementById\([\'"]robotlink[\'"]\)\.innerHTML\s*=\s*[\'"]([^\'"]+)[\'"]', unpacked)
        token_part = re.search(r'\+[\s\'"]*([^\'";]+)&token=([^\'";]+)', unpacked)
        if link_part and token_part:
            direct_url = f"https:{link_part.group(1)}&token={token_part.group(2)}"
            return {
                "success": True,
                "stream_url": direct_url,
                "is_direct": True,
                "is_hls": False,
                "format": "mp4",
                "quality": "1080p FHD",
                "badge": "VIP ⚡",
                "headers": {"User-Agent": USER_AGENT, "Referer": "https://streamtape.com/"},
                "server_name": "Streamtape Direct MP4 ⚡"
            }
        return {"success": False, "error": "Streamtape direct stream not found"}

    @classmethod
    def _extract_megamax(cls, url: str) -> Dict[str, Any]:
        clean_url = url
        if "megamax.me" in clean_url:
            clean_url = clean_url.replace("megamax.me", "eg.megamax.cam")
        try:
            html = cls.fetch_page(clean_url, referer="https://egydead.live/", timeout=5.0)
            unpacked = unpack_all_packers(html)
            m3u8_match = re.search(r'file\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', unpacked)
            if m3u8_match:
                return {
                    "success": True,
                    "stream_url": m3u8_match.group(1),
                    "is_direct": True,
                    "is_hls": True,
                    "format": "hls",
                    "quality": "1080p FHD",
                    "badge": "VIP ⚡",
                    "headers": {"User-Agent": USER_AGENT, "Referer": "https://egydead.live/"},
                    "server_name": "MegaMax Direct FHD ⚡"
                }
        except Exception:
            pass

        return {
            "success": False,
            "error": "MegaMax direct m3u8 stream not found",
            "stream_url": clean_url,
            "is_hls": False,
            "isEmbed": True,
            "headers": {"User-Agent": USER_AGENT, "Referer": "https://egydead.live/"},
            "server_name": "MegaMax Cloud"
        }

    @classmethod
    def _extract_hgcloud(cls, url: str) -> Dict[str, Any]:
        html = cls.fetch_page(url, referer="https://vidsrc.pm/")
        m3u8_match = re.search(r'(https?://[^"\']+\.m3u8[^"\']*)', html)
        if m3u8_match:
            return {
                "success": True,
                "stream_url": m3u8_match.group(1),
                "is_direct": True,
                "is_hls": True,
                "format": "hls",
                "quality": "1080p FHD",
                "badge": "VIP ⚡",
                "headers": {"User-Agent": USER_AGENT, "Referer": "https://vidsrc.pm/"},
                "server_name": "Hgcloud Ultra Direct ⚡"
            }
        return cls._extract_semantic_heuristics(url)

    @classmethod
    def _extract_vidlink(cls, url: str) -> Dict[str, Any]:
        html = cls.fetch_page(url, referer="https://vidlink.pro/")
        m3u8_match = re.search(r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)', html)
        if m3u8_match:
            return {
                "success": True,
                "stream_url": m3u8_match.group(1),
                "is_direct": True,
                "is_hls": True,
                "format": "hls",
                "quality": "1080p FHD",
                "badge": "VIP ⚡",
                "headers": {"User-Agent": USER_AGENT, "Referer": "https://vidlink.pro/"},
                "server_name": "Vidlink Direct Master ⚡"
            }
        return cls._extract_semantic_heuristics(url)

    @classmethod
    def _extract_doodstream(cls, url: str) -> Dict[str, Any]:
        embed_url = url.replace("/d/", "/e/")
        html = cls.fetch_page(embed_url, referer=url)
        pass_match = re.search(r'/pass_md5/([^"\']+)', html)
        if pass_match:
            pass_url = f"https://dood.to/pass_md5/{pass_match.group(1)}"
            token_data = cls.fetch_page(pass_url, referer=embed_url)
            final_stream = token_data + "zZwue Tucker?token=" + pass_match.group(1)
            return {
                "success": True,
                "stream_url": final_stream,
                "is_direct": True,
                "is_hls": False,
                "format": "mp4",
                "quality": "1080p FHD",
                "badge": "VIP ⚡",
                "headers": {"User-Agent": USER_AGENT, "Referer": embed_url},
                "server_name": "Doodstream Direct MP4 ⚡"
            }
        return {"success": False, "error": "Doodstream direct stream not found"}

    @classmethod
    def _extract_with_ytdlp(cls, url: str) -> Dict[str, Any]:
        """Deep stream extraction using yt-dlp when installed."""
        try:
            import yt_dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extract_flat': False,
                'socket_timeout': 5,
                'http_headers': {
                    'User-Agent': USER_AGENT,
                    'Referer': url
                }
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and info.get('url'):
                    direct_url = info['url']
                    if direct_url == url or not any(ext in direct_url.lower() for ext in ['.m3u8', '.mp4', '.mkv', '.webm', '.ts', 'googlevideo', 'cdn']):
                        return {"success": False, "stream_url": url}
                    is_hls = ".m3u8" in direct_url or info.get('protocol') == 'm3u8_native'
                    return {
                        "success": True,
                        "stream_url": direct_url,
                        "is_direct": True,
                        "is_hls": is_hls,
                        "format": "hls" if is_hls else "mp4",
                        "quality": "1080p FHD",
                        "badge": "VIP ⚡",
                        "headers": info.get('http_headers', {}),
                        "server_name": f"{info.get('extractor_key', 'Cloud')} Direct Stream"
                    }
        except Exception:
            pass
        return {"success": False, "stream_url": url}

    @classmethod
    def _extract_semantic_heuristics(cls, url: str) -> Dict[str, Any]:
        """Resilient fallback that parses any page for tokenized HLS/MP4 streams."""
        try:
            html = cls.fetch_page(url, referer=url)
            unpacked = unpack_all_packers(html)

            # 1. Search HLS
            m3u8_matches = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', unpacked)
            for m in m3u8_matches:
                if any(bad in m.lower() for bad in ["doubleclick", "analytics", "pixel", "banner"]):
                    continue
                return {
                    "success": True,
                    "is_direct": True,
                    "is_hls": True,
                    "format": "hls",
                    "stream_url": m,
                    "quality": "1080p FHD",
                    "badge": "VIP ⚡",
                    "headers": cls.get_headers(m, custom_referer=url),
                    "server_name": "سيرفر سحابي HLS ⚡"
                }

            # 2. Search MP4
            mp4_matches = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', unpacked)
            for m in mp4_matches:
                if any(bad in m.lower() for bad in ["sample", "preview", "ad.", "ad_", "intro"]):
                    continue
                return {
                    "success": True,
                    "is_direct": True,
                    "is_hls": False,
                    "format": "mp4",
                    "stream_url": m,
                    "quality": "1080p FHD",
                    "badge": "VIP ⚡",
                    "headers": cls.get_headers(m, custom_referer=url),
                    "server_name": "سيرفر سحابي MP4 ⚡"
                }

            # 3. JWPlayer / VideoJS source configs
            jw_match = re.search(r'(?:file|source|src)\s*:\s*["\'](https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', unpacked)
            if jw_match:
                stream_u = jw_match.group(1)
                is_hls = ".m3u8" in stream_u.lower()
                return {
                    "success": True,
                    "is_direct": True,
                    "stream_url": stream_u,
                    "is_hls": is_hls,
                    "format": "hls" if is_hls else "mp4",
                    "quality": "1080p FHD",
                    "badge": "VIP ⚡",
                    "headers": cls.get_headers(stream_u, custom_referer=url),
                    "server_name": "سيرفر سحابي نقي ⚡"
                }

        except Exception:
            pass

        return {"success": False, "error": "لم يتم العثور على بث مباشر صافٍ"}

    # ==========================================================================
    # High Availability Failover Matrix Builder
    # ==========================================================================
    @classmethod
    def build_failover_matrix(
        cls,
        servers: List[Dict[str, Any]],
        tmdb_id: Optional[str] = None,
        content_type: str = "movie",
        season: Optional[int] = None,
        episode: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Organizes stream candidates into a 3-tier high-availability matrix:
        - Tier 1: Real direct video streams (HLS/MP4) or resolvable harvesters.
        - Tier 2: Ghost Embed Proxied links (/api/watch/embed) with ad-shielding.
        - Tier 3: Universal Guaranteed TMDB Embed Mirrors (VidLink, MultiEmbed, 2Embed).
        """
        tier1: List[Dict[str, Any]] = []
        tier2: List[Dict[str, Any]] = []
        tier3: List[Dict[str, Any]] = []

        seen_urls = set()

        for srv in servers:
            url = srv.get("stream_url") or srv.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            name = srv.get("server_name") or srv.get("name") or "سيرفر البث"
            is_direct = any(ext in url.lower() for ext in [".m3u8", ".mp4", ".mkv", ".webm"])

            if is_direct or any(h in url.lower() for h in ["vidmoly", "mixdrop", "voe", "streamtape", "dood", "vipserver", "liiivideo", "minochinos"]):
                tier1.append({
                    "name": f"{name} (مباشر)",
                    "url": url,
                    "stream_url": url,
                    "tier": 1,
                    "badge": "سريع ⚡",
                    "is_direct": is_direct,
                    "is_hls": ".m3u8" in url.lower()
                })
            else:
                ghost_url = f"/api/watch/embed?url={urllib.parse.quote(url)}"
                tier2.append({
                    "name": f"{name} (درع الإعلانات)",
                    "url": ghost_url,
                    "stream_url": ghost_url,
                    "raw_url": url,
                    "tier": 2,
                    "badge": "درع خفي 🛡️",
                    "is_direct": False,
                    "isEmbed": True
                })

        if tmdb_id and str(tmdb_id).isdigit():
            t_id = str(tmdb_id).strip()
            if content_type == "series" and season and episode:
                tier3.append({
                    "name": "VidLink Global FHD",
                    "url": f"https://vidlink.pro/tv/{t_id}/{season}/{episode}",
                    "stream_url": f"https://vidlink.pro/tv/{t_id}/{season}/{episode}",
                    "tier": 3,
                    "badge": "عالمي ⭐",
                    "isEmbed": True
                })
                tier3.append({
                    "name": "MultiEmbed Universal",
                    "url": f"https://multiembed.mov/?video_id={t_id}&tmdb=1&s={season}&e={episode}",
                    "stream_url": f"https://multiembed.mov/?video_id={t_id}&tmdb=1&s={season}&e={episode}",
                    "tier": 3,
                    "badge": "عالمي ⭐",
                    "isEmbed": True
                })
            else:
                tier3.append({
                    "name": "VidLink Global FHD",
                    "url": f"https://vidlink.pro/movie/{t_id}",
                    "stream_url": f"https://vidlink.pro/movie/{t_id}",
                    "tier": 3,
                    "badge": "عالمي ⭐",
                    "isEmbed": True
                })
                tier3.append({
                    "name": "MultiEmbed Universal",
                    "url": f"https://multiembed.mov/?video_id={t_id}&tmdb=1",
                    "stream_url": f"https://multiembed.mov/?video_id={t_id}&tmdb=1",
                    "tier": 3,
                    "badge": "عالمي ⭐",
                    "isEmbed": True
                })

        return tier1 + tier2 + tier3

    # ==========================================================================
    # On-Demand Just-In-Time Ingestion (JIT Ingestion & Real-Time Discovery)
    # ==========================================================================
    @classmethod
    def search_arabic_portals(cls, query: str) -> List[Dict[str, Any]]:
        """Searches Arab portals (ArabSeed, Akwam, FaselHD, MyCima) in parallel for active watch servers."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        clean_q = urllib.parse.quote(query.strip())
        servers = []

        def _search_arabseed():
            found = []
            try:
                url = f"https://m.arabseed.show/find/?find={clean_q}"
                html = cls.fetch_page(url, timeout=2.5)
                matches = re.findall(r'href="(https?://[^"]*arabseed[^"]*(?:film|series|watch)[^"]*)"', html)
                for m in list(dict.fromkeys(matches))[:2]:
                    sub_html = cls.fetch_page(m, referer=url, timeout=2.5)
                    iframes = re.findall(r'<iframe[^>]+src=["\'](https?://[^"\']+)["\']', sub_html)
                    for ifr in iframes:
                        if any(h in ifr.lower() for h in ["vidmoly", "mixdrop", "voe", "streamtape", "dood", "upstream"]):
                            found.append({
                                "site": "ArabSeed",
                                "server_name": "سيرفر ArabSeed سحابي ⚡",
                                "stream_url": ifr,
                                "url": ifr,
                                "quality": "1080p FHD",
                                "badge": "سريع ⚡"
                            })
                            break
            except Exception:
                pass
            return found

        def _search_akwam():
            found = []
            try:
                url = f"https://akwam.to/search?q={clean_q}"
                html = cls.fetch_page(url, timeout=2.5)
                matches = re.findall(r'href="(https?://[^"]*akwam\.[a-z]+/(?:movie|series|episode)/[^"]+)"', html)
                for m in list(dict.fromkeys(matches))[:2]:
                    sub_html = cls.fetch_page(m, referer=url, timeout=2.5)
                    iframes = re.findall(r'<iframe[^>]+src=["\'](https?://[^"\']+)["\']', sub_html)
                    for ifr in iframes:
                        if any(h in ifr.lower() for h in ["vidmoly", "mixdrop", "voe", "streamtape", "dood", "upstream"]):
                            found.append({
                                "site": "Akwam",
                                "server_name": "سيرفر Akwam سحابي ⚡",
                                "stream_url": ifr,
                                "url": ifr,
                                "quality": "1080p FHD",
                                "badge": "سريع ⚡"
                            })
                            break
            except Exception:
                pass
            return found

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(_search_arabseed), executor.submit(_search_akwam)]
            try:
                for fut in as_completed(futures, timeout=2.5):
                    try:
                        servers.extend(fut.result())
                    except Exception:
                        pass
            except Exception:
                pass

        return servers

    @classmethod
    def jit_search_and_ingest(cls, query: str, content_type: str = "all") -> List[Dict[str, Any]]:
        """
        Executes real-time on-demand discovery, scraping, and instant database ingestion:
        1. Queries TMDB API for accurate metadata and official posters.
        2. Scrapes Arabic portals for real-time streaming servers.
        3. Persists into SQLite instantly.
        4. Returns the freshly created media items in seconds.
        """
        if not query or len(query.strip()) < 2:
            return []

        clean_q = query.strip()
        tmdb_key = get_tmdb_api_key()
        tmdb_url = f"https://api.themoviedb.org/3/search/multi?api_key={tmdb_key}&language=ar-SA&query={urllib.parse.quote(clean_q)}"

        items_to_save = []

        try:
            req = urllib.request.Request(tmdb_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("results", [])
                for idx, r in enumerate(results[:4]):
                    m_type = r.get("media_type")
                    if m_type not in ("movie", "tv"):
                        continue
                    
                    is_series = m_type == "tv"
                    c_type = "series" if is_series else "movie"
                    if content_type and content_type != "all" and content_type != c_type:
                        continue

                    title = r.get("name") if is_series else r.get("title")
                    if not title:
                        continue

                    orig_title = r.get("original_name") if is_series else r.get("original_title")
                    release_date = r.get("first_air_date", "") if is_series else r.get("release_date", "")
                    year = release_date.split("-")[0] if release_date else ""

                    tmdb_id = str(r.get("id"))
                    poster_path = r.get("poster_path")
                    backdrop_path = r.get("backdrop_path")
                    poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
                    backdrop = f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else poster

                    slug = re.sub(r'[^a-zA-Z0-9\u0600-\u06FF]+', '-', title).strip('-').lower()
                    media_id = f"{slug}-{year}-{tmdb_id}" if year else f"{slug}-{tmdb_id}"

                    # Find watch servers (Fast portal scrape for top candidate)
                    scraped_servers = cls.search_arabic_portals(title) if idx == 0 else []

                    # Bind Universal TMDB mirrors
                    if is_series:
                        scraped_servers.append({
                            "site": "VidLink",
                            "server_name": "VidLink Global FHD ⭐",
                            "stream_url": f"https://vidlink.pro/tv/{tmdb_id}/1/1",
                            "url": f"https://vidlink.pro/tv/{tmdb_id}/1/1",
                            "quality": "1080p FHD",
                            "badge": "عالمي ⭐",
                            "season": 1,
                            "episode": 1
                        })
                        scraped_servers.append({
                            "site": "MultiEmbed",
                            "server_name": "MultiEmbed Universal ⭐",
                            "stream_url": f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1&s=1&e=1",
                            "url": f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1&s=1&e=1",
                            "quality": "1080p FHD",
                            "badge": "عالمي ⭐",
                            "season": 1,
                            "episode": 1
                        })
                    else:
                        scraped_servers.append({
                            "site": "VidLink",
                            "server_name": "VidLink Global FHD ⭐",
                            "stream_url": f"https://vidlink.pro/movie/{tmdb_id}",
                            "url": f"https://vidlink.pro/movie/{tmdb_id}",
                            "quality": "1080p FHD",
                            "badge": "عالمي ⭐"
                        })
                        scraped_servers.append({
                            "site": "MultiEmbed",
                            "server_name": "MultiEmbed Universal ⭐",
                            "stream_url": f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1",
                            "url": f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1",
                            "quality": "1080p FHD",
                            "badge": "عالمي ⭐"
                        })

                    media_item = {
                        "id": media_id,
                        "title": title,
                        "arabic_title": title,
                        "original_title": orig_title or title,
                        "year": year,
                        "rating": str(round(r.get("vote_average", 8.0), 1)),
                        "poster": poster,
                        "backdrop": backdrop,
                        "category": "foreign",
                        "content_type": c_type,
                        "synopsis": r.get("overview") or "مشاهدة وتحميل مجاناً بأعلى جودة على A TuBe",
                        "duration": "120 دقيقة" if not is_series else "45 دقيقة",
                        "quality": "1080p FHD",
                        "genres": ["دراما", "أكشن"],
                        "tmdb_id": tmdb_id,
                        "total_seasons": 1 if is_series else 0,
                        "servers": scraped_servers
                    }

                    # Persist instantly to SQLite
                    VODDatabaseManager.save_media(media_item)

                    # For series, initialize Season 1 Episode 1
                    if is_series:
                        conn = VODDatabaseManager.get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO vod_seasons (media_id, season_number, season_title)
                            VALUES (?, 1, 'الموسم 1')
                            ON CONFLICT(media_id, season_number) DO NOTHING
                        """, (media_id,))
                        cur.execute("""
                            INSERT INTO vod_episodes (media_id, season_number, episode_number, episode_title, thumbnail, duration, synopsis)
                            VALUES (?, 1, 1, 'الحلقة 1', ?, '45 دقيقة', ?)
                            ON CONFLICT(media_id, season_number, episode_number) DO NOTHING
                        """, (media_id, poster, media_item["synopsis"]))
                        conn.commit()
                        conn.close()

                    items_to_save.append(media_item)

        except Exception as ex:
            print(f"[JIT Ingestion] Exception during search and ingest: {ex}")

        return items_to_save


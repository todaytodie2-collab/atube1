# -*- coding: utf-8 -*-
"""
A TuBe Streams Engine - Stream Bridge & HLS Playlist Rewriter
Handles proxying stream requests, anti-hotlinking referer spoofing, and dynamic M3U8 chunk rewriting.
"""

import re
import urllib.parse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Tuple
from config import USER_AGENT, HOST_SPOOF_MAP

_proxy_session = None

def get_proxy_session() -> requests.Session:
    global _proxy_session
    if _proxy_session is None:
        s = requests.Session()
        retries = Retry(total=2, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(pool_connections=64, pool_maxsize=128, max_retries=retries)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        _proxy_session = s
    return _proxy_session

def get_spoofed_headers(target_url: str, referer: str = "") -> Dict[str, str]:
    """Builds appropriate anti-hotlinking headers for a target streaming host."""
    proxy_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Encoding": "identity",
        "Connection": "keep-alive"
    }

    if referer:
        proxy_headers["Referer"] = referer
        parsed_ref = urllib.parse.urlparse(referer)
        if parsed_ref.scheme and parsed_ref.netloc:
            proxy_headers["Origin"] = f"{parsed_ref.scheme}://{parsed_ref.netloc}"
    else:
        for kw, (ref_url, origin_url) in HOST_SPOOF_MAP.items():
            if kw in target_url.lower():
                proxy_headers["Referer"] = ref_url
                proxy_headers["Origin"] = origin_url
                break

    return proxy_headers

def rewrite_hls_playlist(body_text: str, target_url: str, referer: str = "") -> str:
    """Rewrites relative/absolute URLs in an M3U8 playlist to route through the local proxy."""
    rewritten_lines = []
    for line in body_text.splitlines():
        s_line = line.strip()
        if not s_line:
            rewritten_lines.append(line)
            continue

        if s_line.startswith("#") and 'URI="' in s_line:
            def _rep_uri(m):
                sub_uri = m.group(1)
                joined = urllib.parse.urljoin(target_url, sub_uri)
                proxy_sub = f"/api/stream/proxy?url={urllib.parse.quote(joined, safe='')}"
                if referer:
                    proxy_sub += f"&referer={urllib.parse.quote(referer, safe='')}"
                return f'URI="{proxy_sub}"'
            s_line = re.sub(r'URI="([^"]+)"', _rep_uri, s_line)
            rewritten_lines.append(s_line)
        elif not s_line.startswith("#"):
            joined = urllib.parse.urljoin(target_url, s_line)
            proxy_chunk = f"/api/stream/proxy?url={urllib.parse.quote(joined, safe='')}"
            if referer:
                proxy_chunk += f"&referer={urllib.parse.quote(referer, safe='')}"
            rewritten_lines.append(proxy_chunk)
        else:
            rewritten_lines.append(line)

    return "\n".join(rewritten_lines)

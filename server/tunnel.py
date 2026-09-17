# -*- coding: utf-8 -*-
"""
A TuBe Server - Networking, IPv6 Bridge & Cloudflare Tunnel
"""

import os
import time
import socket
import threading
import subprocess
import urllib.request
import json
from config import PROJECT_ROOT
from server.app import logger

_current_tunnel_url = ""

def get_current_tunnel_url() -> str:
    global _current_tunnel_url
    if _current_tunnel_url:
        return _current_tunnel_url
    url_file = os.path.join(PROJECT_ROOT, "logs", "current_tunnel_url.txt")
    if os.path.exists(url_file):
        try:
            with open(url_file, "r", encoding="utf-8") as f:
                _current_tunnel_url = f.read().strip()
        except Exception:
            pass
    return _current_tunnel_url

def start_ipv6_loopback_bridge(port: int = 8085):
    """Starts an IPv6 to IPv4 loopback bridge for [::1] on port."""
    def bridge_worker():
        try:
            s_in = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s_in.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s_in.bind(("::1", port))
            s_in.listen(64)
            logger.info(f"[Network] IPv6 loopback bridge active on [::1]:{port} -> 127.0.0.1:{port}")
            while True:
                client_sock, _ = s_in.accept()
                def forward(src, dst):
                    try:
                        while True:
                            d = src.recv(32768)
                            if not d:
                                break
                            dst.sendall(d)
                    except Exception:
                        pass
                    finally:
                        try: src.close()
                        except Exception: pass
                        try: dst.close()
                        except Exception: pass

                try:
                    target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    target_sock.connect(("127.0.0.1", port))
                    threading.Thread(target=forward, args=(client_sock, target_sock), daemon=True).start()
                    threading.Thread(target=forward, args=(target_sock, client_sock), daemon=True).start()
                except Exception:
                    try: client_sock.close()
                    except Exception: pass
        except Exception as e:
            logger.warning(f"[Network] IPv6 bridge could not start on [::1]:{port} ({e})")

    t = threading.Thread(target=bridge_worker, daemon=True)
    t.start()

def start_cloudflare_tunnel(port: int = 8085, metrics_port: int = 20240):
    """Launches Cloudflare Quick Tunnel in the background and registers URL."""
    global _current_tunnel_url
    cf_bin = os.path.join(PROJECT_ROOT, "tools", "cloudflared.exe")
    if not os.path.exists(cf_bin):
        cf_bin = os.path.join(PROJECT_ROOT, "cloudflared.exe")
    if not os.path.exists(cf_bin):
        cf_bin = "cloudflared"

    def runner():
        global _current_tunnel_url
        try:
            try:
                m_url = f"http://127.0.0.1:{metrics_port}/quicktunnel"
                req = urllib.request.Request(m_url)
                with urllib.request.urlopen(req, timeout=1.5) as r:
                    data = json.loads(r.read().decode('utf-8'))
                    hostname = data.get("hostname")
                    if hostname:
                        _current_tunnel_url = f"https://{hostname}"
                        logger.info(f"[Cloudflare] Quick Tunnel already active: {_current_tunnel_url}")
                        return
            except Exception:
                pass

            cmd = [
                cf_bin, "tunnel",
                "--url", f"http://127.0.0.1:{port}",
                "--metrics", f"127.0.0.1:{metrics_port}",
                "--no-autoupdate"
            ]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            logger.info(f"[Cloudflare] Quick Tunnel process started (PID {proc.pid})")

            for _ in range(30):
                time.sleep(1.0)
                try:
                    m_url = f"http://127.0.0.1:{metrics_port}/quicktunnel"
                    req = urllib.request.Request(m_url)
                    with urllib.request.urlopen(req, timeout=1.5) as r:
                        data = json.loads(r.read().decode('utf-8'))
                        hostname = data.get("hostname")
                        if hostname:
                            _current_tunnel_url = f"https://{hostname}"
                            logger.info(f"[Cloudflare] Quick Tunnel LIVE: {_current_tunnel_url}")
                            url_file = os.path.join(PROJECT_ROOT, "logs", "current_tunnel_url.txt")
                            try:
                                with open(url_file, "w", encoding="utf-8") as f:
                                    f.write(_current_tunnel_url + "\n")
                            except Exception:
                                pass
                            
                            # Auto-sync to GitHub Pages / Gist in background
                            def _bg_sync():
                                try:
                                    from tools.github_redirect_sync import sync_tunnel_url
                                    sync_tunnel_url(_current_tunnel_url)
                                except Exception as e_sync:
                                    logger.warning(f"[GitHub Sync] Auto-sync failed: {e_sync}")
                            threading.Thread(target=_bg_sync, daemon=True).start()
                            break
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"[Cloudflare] Could not launch tunnel: {e}")

    t = threading.Thread(target=runner, daemon=True)
    t.start()

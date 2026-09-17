# -*- coding: utf-8 -*-
"""
A TuBe Clean Architecture - Primary Flask Server & API Gateway Facade
"""

import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from server import (
    app,
    run_server,
    get_lan_ip,
    get_current_tunnel_url,
    start_ipv6_loopback_bridge,
    start_cloudflare_tunnel
)

if __name__ == "__main__":
    run_server()
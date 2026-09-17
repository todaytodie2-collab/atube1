# -*- coding: utf-8 -*-
"""
A TuBe Server Package - Primary Application & API Gateway
"""

import os
from flask import send_from_directory, jsonify
from config import PROJECT_ROOT, SERVER_HOST, SERVER_PORT, DEBUG_MODE
from database import VODDatabaseManager
from media_catalog.series_completer import SeriesCompleter
from server.app import app, get_lan_ip, logger, FRONTEND_DIR
from server.routes.media_routes import media_bp
from server.routes.stream_routes import stream_bp
from server.routes.tv_routes import tv_bp
from server.routes.admin_routes import admin_bp
from server.tunnel import start_ipv6_loopback_bridge, start_cloudflare_tunnel, get_current_tunnel_url

# Register Blueprints
app.register_blueprint(media_bp)
app.register_blueprint(stream_bp)
app.register_blueprint(tv_bp)
app.register_blueprint(admin_bp)

# Fallback Static File Handler
@app.route("/<path:path>", methods=["GET"])
def serve_fallback_static(path):
    # Try serving from frontend directory first
    front_path = os.path.abspath(os.path.join(FRONTEND_DIR, path))
    front_root = os.path.abspath(FRONTEND_DIR)
    if front_path.startswith(front_root) and os.path.exists(front_path) and os.path.isfile(front_path):
        return send_from_directory(FRONTEND_DIR, path)

    # Fallback to project root if applicable
    full_path = os.path.abspath(os.path.join(PROJECT_ROOT, path))
    root_path = os.path.abspath(PROJECT_ROOT)
    if not full_path.startswith(root_path):
        logger.warning(f"[Security] Blocked path traversal attempt: {path}")
        return jsonify({"error": "Access Denied"}), 403

    if os.path.exists(full_path) and os.path.isfile(full_path):
        return send_from_directory(PROJECT_ROOT, path)
    return jsonify({"error": "Not Found"}), 404

def run_server():
    """Starts all background workers and launches Flask HTTP server."""
    VODDatabaseManager.init_db()
    lan_ip = get_lan_ip()
    stats = VODDatabaseManager.get_stats()

    print("=" * 68)
    print("  🚀 A TuBe Ultra HD (Modular Clean Architecture) Gateway")
    print(f"  📺 Localhost URL : http://localhost:{SERVER_PORT}/index.html")
    print(f"  🌐 LAN IP URL    : http://{lan_ip}:{SERVER_PORT}/index.html")
    print(f"  📂 DB Path       : {stats['db_path']}")
    print(f"  📊 Media Count   : {stats['total_media']} Titles | {stats['total_servers']} Servers")
    print(f"  📝 Log File      : logs/atube.log")
    print("=" * 68)

    from scrapers.auto_harvester import AutoHarvesterScheduler
    AutoHarvesterScheduler.start_periodic_scheduler(interval_hours=6)
    SeriesCompleter.start_background_worker(interval_hours=4)
    start_ipv6_loopback_bridge(SERVER_PORT)
    start_cloudflare_tunnel(SERVER_PORT)
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)

__all__ = [
    "app",
    "run_server",
    "get_lan_ip",
    "get_current_tunnel_url",
    "start_ipv6_loopback_bridge",
    "start_cloudflare_tunnel"
]

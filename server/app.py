# -*- coding: utf-8 -*-
"""
A TuBe Server - Core Flask Application & Static Serving
"""

import os
import sys
import socket
import urllib.parse
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from config import BASE_DIR, PROJECT_ROOT, DB_PATH
from database import VODDatabaseManager

FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# Configure Centralized Logging
log_dir = os.path.join(BASE_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "atube.log")

logger = logging.getLogger("atube")
logger.setLevel(logging.INFO)
if not logger.handlers:
    file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    try:
        file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError):
        pass

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(file_formatter)
    logger.addHandler(console_handler)

def get_lan_ip() -> str:
    """Discovers the local LAN IP of the workstation."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def is_safe_url(url: str) -> bool:
    """SSRF Guard: validates external URLs and blocks loopback addresses."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = (parsed.hostname or "").lower()
        if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254"):
            return False
        return True
    except Exception:
        return False

# Create Flask Application
app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS", "HEAD"],
    "allow_headers": ["*"],
    "expose_headers": ["Content-Range", "Accept-Ranges", "Content-Length", "Content-Type"]
}})

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "Content-Range, Accept-Ranges, Content-Length, Content-Type"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

# Static Web App Routes
@app.route("/", methods=["GET"])
@app.route("/index.html", methods=["GET"])
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/assets/<path:path>", methods=["GET"])
def serve_assets(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, "assets"), path)

@app.route("/js/<path:path>", methods=["GET"])
def serve_js(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, "js"), path)

@app.route("/css/<path:path>", methods=["GET"])
def serve_css(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, "css"), path)

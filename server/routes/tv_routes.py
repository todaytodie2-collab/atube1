# -*- coding: utf-8 -*-
"""
A TuBe Server - Live TV API Routes (/api/channels, /api/live_tv/*)
"""

from flask import Blueprint, request, jsonify
from live_tv.manager import LiveTVManager

tv_bp = Blueprint("tv_bp", __name__)

@tv_bp.route("/api/channels", methods=["GET"])
@tv_bp.route("/api/iptv/verified", methods=["GET"])
@tv_bp.route("/api/live_tv/channels", methods=["GET"])
def api_channels():
    cat = request.args.get("cat", "") or request.args.get("category", "")
    search = request.args.get("q", "") or request.args.get("search", "")
    channels = LiveTVManager.get_channels(category=cat, search=search)
    return jsonify(channels)

@tv_bp.route("/api/live_tv/categories", methods=["GET"])
def api_live_categories():
    return jsonify(LiveTVManager.get_categories())

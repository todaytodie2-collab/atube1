# -*- coding: utf-8 -*-
"""
A TuBe Server - Media Catalog API Routes (/api/media/*)
"""

from flask import Blueprint, request, jsonify
from database import VODDatabaseManager
from streams.jit_engine import JITStreamEngine
from config import CATEGORY_MAP

media_bp = Blueprint("media_bp", __name__)

@media_bp.route("/api/media/feed", methods=["GET"])
def api_feed():
    c_type = request.args.get("type", "all")
    category = request.args.get("category", "all")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 40))
    search = request.args.get("search", "") or request.args.get("q", "")

    if category in CATEGORY_MAP:
        c_type, category = CATEGORY_MAP[category]

    feed = VODDatabaseManager.get_feed(
        content_type=c_type,
        category=category,
        page=page,
        limit=limit,
        search=search
    )

    if search and feed.get("total_items", 0) == 0:
        ingested = JITStreamEngine.jit_search_and_ingest(search, content_type=c_type)
        if ingested:
            feed = VODDatabaseManager.get_feed(
                content_type=c_type,
                category=category,
                page=page,
                limit=limit,
                search=search
            )

    return jsonify(feed)

@media_bp.route("/api/media/details", methods=["GET"])
def api_details():
    media_id = request.args.get("id", "")
    if not media_id:
        return jsonify({"error": "Missing media id"}), 400

    details = VODDatabaseManager.get_details(media_id)
    if not details:
        ingested = JITStreamEngine.jit_search_and_ingest(media_id)
        if ingested:
            details = VODDatabaseManager.get_details(ingested[0]["id"])

    if not details:
        return jsonify({"error": "Media not found"}), 404

    return jsonify(details)

@media_bp.route("/api/media/cast", methods=["GET"])
def api_cast():
    media_id = request.args.get("id", "")
    if not media_id:
        return jsonify([])
    cast = VODDatabaseManager.get_cast(media_id)
    return jsonify(cast)

@media_bp.route("/api/media/episodes", methods=["GET"])
def api_episodes():
    media_id = request.args.get("id", "")
    season = int(request.args.get("season", 1))
    if not media_id:
        return jsonify([])
    episodes = VODDatabaseManager.get_episodes(media_id, season)
    return jsonify(episodes)

@media_bp.route("/api/media/recent-episodes", methods=["GET"])
def api_recent_episodes():
    category = request.args.get("category", "all")
    limit = int(request.args.get("limit", 16))
    episodes = VODDatabaseManager.get_recent_episodes(category=category, limit=limit)
    return jsonify(episodes)

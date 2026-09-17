# -*- coding: utf-8 -*-
"""
A TuBe Server - Admin & Harvester API Routes (/api/admin/*, /api/harvester/*, /api/health)
"""

import os
import threading
from flask import Blueprint, request, jsonify
from database import VODDatabaseManager
from media_catalog.data_repair import DataRepairEngine
from scrapers.universal.universal_harvester import UniversalHarvester, CATEGORIES_REGISTRY, PROVIDERS
from server.tunnel import get_current_tunnel_url
from server.app import get_lan_ip, logger
from config import SERVER_PORT

admin_bp = Blueprint("admin_bp", __name__)

@admin_bp.route("/api/health", methods=["GET"])
@admin_bp.route("/api/status", methods=["GET"])
def api_health():
    stats = VODDatabaseManager.get_stats()
    return jsonify({
        "status": "healthy",
        "service": "A TuBe Ultra HD (v2.5)",
        "lan_ip": get_lan_ip(),
        "port": SERVER_PORT,
        "tunnel_url": get_current_tunnel_url(),
        "stats": {
            "media_count": stats["total_media"],
            "servers_count": stats["total_servers"],
            "episodes_count": stats["total_episodes"]
        }
    })

@admin_bp.route("/api/admin/repair", methods=["POST"])
def api_admin_repair():
    result = DataRepairEngine.optimize_database()
    return jsonify(result)

@admin_bp.route("/api/harvester/categories", methods=["GET"])
def api_harvester_categories():
    counts = {}
    try:
        conn = VODDatabaseManager.get_connection()
        cur = conn.cursor()
        for cat_key, cat_info in CATEGORIES_REGISTRY.items():
            cur.execute(
                "SELECT COUNT(*) FROM vod_media WHERE category = ? AND (content_type = ? OR type = ?)",
                (cat_info["category"], cat_info["content_type"], cat_info["content_type"])
            )
            row = cur.fetchone()
            counts[cat_key] = row[0] if row else 0
        conn.close()
    except Exception as e:
        logger.error(f"[Harvester API] Category counts error: {e}")

    result = []
    for cat_key, cat_info in CATEGORIES_REGISTRY.items():
        result.append({
            "key": cat_key,
            "label": cat_info["label"],
            "icon": cat_info["icon"],
            "category": cat_info["category"],
            "content_type": cat_info["content_type"],
            "count": counts.get(cat_key, 0)
        })
    return jsonify({"categories": result, "providers": list(PROVIDERS.keys())})

@admin_bp.route("/api/harvester/start", methods=["POST"])
def api_harvester_start():
    data = request.get_json(silent=True) or request.form or {}
    category = data.get("category", "arabic_series")
    provider = data.get("provider", "EgyDead")
    start_page = int(data.get("start_page", 1))
    max_pages = data.get("max_pages")
    if max_pages is not None:
        try:
            max_pages = int(max_pages)
        except Exception:
            max_pages = None

    if category not in CATEGORIES_REGISTRY:
        return jsonify({"success": False, "error": f"Unknown category: {category}"}), 400

    job_id = UniversalHarvester.start_infinite_harvest(
        provider_name=provider,
        category_key=category,
        start_page=start_page,
        max_pages=max_pages
    )

    return jsonify({
        "success": True,
        "job_id": job_id,
        "message": f"بدأ سحب {CATEGORIES_REGISTRY[category]['label']} من {provider} (الصفحات: {'غير محدودة' if max_pages is None else max_pages})"
    })

@admin_bp.route("/api/harvester/status", methods=["GET"])
def api_harvester_status():
    job_id = request.args.get("job_id")
    if job_id:
        st = UniversalHarvester.get_job_status(job_id)
        if not st:
            return jsonify({"error": "Job not found"}), 404
        return jsonify(st)
    return jsonify({"jobs": UniversalHarvester.get_all_jobs()})

# Multi-Portal Playwright Auto Harvester Endpoints
@admin_bp.route("/api/auto-harvester/start", methods=["POST"])
def api_auto_harvester_start():
    from scrapers.auto_harvester import AutoHarvesterScheduler
    data = request.get_json(silent=True) or request.form or {}
    provider = data.get("provider")
    category = data.get("category")
    max_pages = int(data.get("max_pages", 2))

    started = AutoHarvesterScheduler.start_job_async(
        provider=provider,
        category=category,
        max_pages=max_pages
    )
    if started:
        return jsonify({
            "success": True,
            "message": f"تم بدء جلسة السحب الآلي للمنصات ({provider or 'جميع المواقع'}).",
            "status": AutoHarvesterScheduler.get_status()
        })
    return jsonify({
        "success": False,
        "message": "عملية السحب قيد التشغيل بالفعل.",
        "status": AutoHarvesterScheduler.get_status()
    }), 409

@admin_bp.route("/api/auto-harvester/status", methods=["GET"])
def api_auto_harvester_status():
    from scrapers.auto_harvester import AutoHarvesterScheduler
    return jsonify(AutoHarvesterScheduler.get_status())

@admin_bp.route("/api/auto-harvester/stop", methods=["POST"])
def api_auto_harvester_stop():
    from scrapers.auto_harvester import AutoHarvesterScheduler
    AutoHarvesterScheduler.stop_current_job()
    return jsonify({"success": True, "message": "تم إرسال إشارة إيقاف السحب."})

@admin_bp.route("/api/admin/restart", methods=["POST", "GET"])
def api_admin_restart():
    def _do_restart():
        import time
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=_do_restart, daemon=True).start()
    return jsonify({"success": True, "message": "Server restarting under service watchdog..."})


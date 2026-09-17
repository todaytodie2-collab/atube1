# -*- coding: utf-8 -*-
"""
A TuBe Auto Harvester - Background Scheduler & Task Manager
Handles periodic automated crawling (every 6 hours) and on-demand scraping jobs.
"""

import os
import threading
import asyncio
import time
from typing import Dict, Any, Optional
from scrapers.auto_harvester.scraper import (
    run_auto_harvester_job,
    get_harvest_state,
    stop_harvest,
    HARVESTER_ROUTES_MAP
)

class AutoHarvesterScheduler:
    """Manages scheduled and on-demand background harvesting jobs."""
    _thread: Optional[threading.Thread] = None
    _scheduler_thread: Optional[threading.Thread] = None
    _is_scheduler_running: bool = False
    _interval_hours: int = 6
    _next_run_timestamp: Optional[float] = None
    _last_run_timestamp: Optional[float] = None

    @classmethod
    def start_job_async(cls, provider: Optional[str] = None, category: Optional[str] = None, max_pages: int = 2) -> bool:
        """Launches a single harvest job in a dedicated background thread."""
        state = get_harvest_state()
        if state.get("is_running"):
            return False

        cls._last_run_timestamp = time.time()

        def _worker():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_auto_harvester_job(
                    target_provider=provider,
                    target_category=category,
                    max_pages=max_pages
                ))
            finally:
                loop.close()

        cls._thread = threading.Thread(target=_worker, daemon=True, name="AutoHarvesterWorker")
        cls._thread.start()
        return True

    @classmethod
    def stop_current_job(cls):
        """Requests the active crawler to finish current item and stop."""
        stop_harvest()

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns the current state and list of available providers with scheduling timestamps."""
        state = get_harvest_state()
        state["available_providers"] = list(HARVESTER_ROUTES_MAP.keys())
        state["scheduler_active"] = cls._is_scheduler_running
        state["interval_hours"] = cls._interval_hours
        state["next_run_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(cls._next_run_timestamp)) if cls._next_run_timestamp else None
        state["last_run_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(cls._last_run_timestamp)) if cls._last_run_timestamp else None
        return state

    @classmethod
    def start_periodic_scheduler(cls, interval_hours: int = 6):
        """Starts a standing background daemon that triggers a harvest cycle every `interval_hours` (default 6h)."""
        if cls._is_scheduler_running:
            return

        cls._interval_hours = int(os.environ.get("HARVEST_INTERVAL_HOURS", interval_hours))
        cls._is_scheduler_running = True

        def _scheduler_loop():
            # Initial startup delay (60 seconds) so the server starts cleanly
            cls._next_run_timestamp = time.time() + 60
            print(f"[⏰ AutoHarvesterScheduler] تم تفعيل الجدولة التلقائية: دورة كشط كل {cls._interval_hours} ساعات.")
            
            time.sleep(60)
            
            while cls._is_scheduler_running:
                try:
                    print(f"\n[⏰ AutoHarvesterScheduler] حان موعد دورة الكشط المجدولة (كل {cls._interval_hours} ساعات)...")
                    cls.start_job_async(max_pages=2)
                except Exception as e:
                    print(f"[!] خطأ أثناء بدء دورة الكشط الدورية: {e}")

                # Calculate next run timestamp (6 hours from now)
                sleep_seconds = cls._interval_hours * 3600
                cls._next_run_timestamp = time.time() + sleep_seconds
                
                # Sleep in increments of 10s to allow clean shutdown
                for _ in range(sleep_seconds // 10):
                    if not cls._is_scheduler_running:
                        break
                    time.sleep(10)

        cls._scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True, name="AutoHarvesterScheduler")
        cls._scheduler_thread.start()

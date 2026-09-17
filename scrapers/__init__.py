# -*- coding: utf-8 -*-
"""
A TuBe Scrapers Package
Contains scrapers for Arabic and international streaming sources.
"""

from scrapers.base_scraper import BaseScraper
from scrapers.egydead.scraper import scrape_egydead
from scrapers.universal.universal_harvester import UniversalHarvester
from scrapers.auto_harvester import AutoHarvesterScheduler, run_auto_harvester_job

__all__ = [
    "BaseScraper",
    "scrape_egydead",
    "UniversalHarvester",
    "AutoHarvesterScheduler",
    "run_auto_harvester_job"
]

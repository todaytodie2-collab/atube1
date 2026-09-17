# -*- coding: utf-8 -*-
"""
A TuBe - Cloud Auto Harvester Engine (GitHub Actions & Cloud Runner Optimized)
Autonomous 8-Hour Scheduled Harvester for 10 Streaming Portals.
Enriches scraped content with TMDB metadata, extracts direct embed/stream servers,
and updates SQLite DB + exports JSON catalog.
"""

import os
import sys
import json
import re
import time
import argparse
import asyncio
import datetime
from typing import Dict, Any, List, Optional, Tuple
from playwright.async_api import async_playwright

# Setup base paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from database import VODDatabaseManager
from posters_engine.tmdb_service import TMDBService
from scrapers.auto_harvester.scraper import (
    HARVESTER_ROUTES_MAP,
    parse_series_title_and_episode,
    determine_content_type
)
from config import DB_PATH, USER_AGENT

EXPORT_JSON_PATH = os.path.join(PROJECT_ROOT, "data", "cloud_harvest_export.json")
SUMMARY_JSON_PATH = os.path.join(PROJECT_ROOT, "data", "cloud_harvest_summary.json")

async def extract_item_details(page, item_url: str, provider: str) -> Dict[str, Any]:
    """Navigates to an item page and extracts stream servers and video embeds."""
    details = {
        "servers": [],
        "episodes": [],
        "synopsis": "",
        "download_links": []
    }
    try:
        await page.goto(item_url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(1.0)
        
        # 1. Search for iframe embed players
        iframes = await page.query_selector_all("iframe")
        for ifr in iframes:
            try:
                src = await ifr.get_attribute("src")
                if src and src.startswith("http") and not any(ad in src for ad in ["google", "ads", "doubleclick", "disqus"]):
                    server_name = "Cloud Server"
                    for kw in ["vidmoly", "mixdrop", "streamtape", "dood", "voe", "upstream", "vidsrc", "vidlink", "autoembed"]:
                        if kw in src.lower():
                            server_name = kw.capitalize()
                            break
                    details["servers"].append({
                        "name": server_name,
                        "url": src,
                        "quality": "1080p",
                        "type": "embed"
                    })
            except Exception:
                pass

        # 2. Search for watch server buttons / data-url / href
        server_btns = await page.query_selector_all("ul.servers-list li, ul.watch-servers li, div.server--item, a.watch-btn, a.btn-server")
        for btn in server_btns:
            try:
                data_url = await btn.get_attribute("data-url") or await btn.get_attribute("data-src") or await btn.get_attribute("href")
                btn_name = (await btn.inner_text()).strip() or "Server HD"
                if data_url and data_url.startswith("http"):
                    details["servers"].append({
                        "name": btn_name,
                        "url": data_url,
                        "quality": "HD",
                        "type": "stream"
                    })
            except Exception:
                pass

        # 3. Extract synopsis if available
        syn_el = await page.query_selector(".story, .overview, .post-entry, .story-movie, .description")
        if syn_el:
            details["synopsis"] = (await syn_el.inner_text()).strip()

    except Exception as e:
        print(f"[!] Error fetching details from {item_url}: {e}")
        
    return details

async def run_cloud_harvester(
    target_providers: Optional[List[str]] = None,
    max_pages: int = 1,
    export_json: bool = True
) -> Dict[str, Any]:
    """Executes headless cloud scraping across configured portals."""
    start_time = time.time()
    active_providers = target_providers if target_providers else list(HARVESTER_ROUTES_MAP.keys())
    
    summary = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "providers_scanned": active_providers,
        "max_pages_per_category": max_pages,
        "total_scanned": 0,
        "total_inserted": 0,
        "new_media_items": [],
        "errors": []
    }
    
    harvested_export = []

    print(f"================================================================")
    print(f"🚀 A TuBe Cloud Harvester Starting (Headless CI Mode)")
    print(f"🎯 Target Providers: {', '.join(active_providers)}")
    print(f"📄 Max Pages per Category: {max_pages}")
    print(f"================================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-first-run",
                "--no-zygote"
            ]
        )
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        page.on("popup", lambda popup: asyncio.create_task(popup.close()))

        for prov_name in active_providers:
            if prov_name not in HARVESTER_ROUTES_MAP:
                continue
                
            prov_data = HARVESTER_ROUTES_MAP[prov_name]
            categories = prov_data["categories"]
            selectors = prov_data["selectors"]
            
            print(f"\n[🌐 Portal] Ingesting portal: {prov_name} ({len(categories)} categories)...")

            for cat_name, cat_url in categories.items():
                content_type = determine_content_type(cat_name)
                print(f"  📂 Category: {cat_name} -> {cat_url}")
                
                for page_idx in range(1, max_pages + 1):
                    target_url = cat_url if page_idx == 1 else f"{cat_url.rstrip('/')}/page/{page_idx}/"
                    try:
                        print(f"    Scanning page {page_idx}: {target_url}...")
                        await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
                        await asyncio.sleep(1.0)
                        
                        cards = await page.query_selector_all(selectors["card"])
                        if not cards:
                            print(f"    [!] No cards found on page {page_idx}.")
                            break

                        for card in cards:
                            summary["total_scanned"] += 1
                            try:
                                # Extract card details
                                title_el = await card.query_selector(selectors["title"])
                                raw_title = (await title_el.inner_text()).strip() if title_el else ""
                                
                                link_el = await card.query_selector("a")
                                item_url = await link_el.get_attribute("href") if link_el else ""
                                
                                img_el = await card.query_selector(selectors["img"])
                                poster_url = ""
                                if img_el:
                                    poster_url = (
                                        await img_el.get_attribute("src") or 
                                        await img_el.get_attribute("data-src") or 
                                        await img_el.get_attribute("data-original") or ""
                                    )
                                    
                                if not raw_title or not item_url:
                                    continue

                                # Metadata parsing & TMDB Enrichment
                                if content_type == "series":
                                    clean_title, s_num, ep_num = parse_series_title_and_episode(raw_title)
                                    tmdb_meta = TMDBService.get_full_metadata(clean_title, content_type="series")
                                    
                                    # Fallback images
                                    final_poster = tmdb_meta.get("poster") or poster_url
                                    final_backdrop = tmdb_meta.get("backdrop") or poster_url
                                    
                                    # Fetch episode stream servers
                                    detail_page = await context.new_page()
                                    detail_page.on("popup", lambda popup: asyncio.create_task(popup.close()))
                                    item_details = await extract_item_details(detail_page, item_url, prov_name)
                                    await detail_page.close()
                                    
                                    servers_list = item_details["servers"]
                                    if not servers_list:
                                        servers_list = [{"name": f"{prov_name} Live", "url": item_url, "quality": "FHD", "type": "embed"}]

                                    # Insert Series + Episode with strict isolation
                                    series_id = VODDatabaseManager.insert_series_episode(
                                        series_title=clean_title,
                                        season_number=s_num,
                                        episode_number=ep_num,
                                        episode_title=f"الحلقة {ep_num}",
                                        servers=servers_list,
                                        category=cat_name,
                                        link=item_url,
                                        poster=final_poster,
                                        backdrop=final_backdrop,
                                        rating=str(tmdb_meta.get("rating", "8.0")),
                                        year=str(tmdb_meta.get("year", "2024")),
                                        genres=tmdb_meta.get("genres", ["مسلسلات"]),
                                        synopsis=tmdb_meta.get("synopsis") or item_details.get("synopsis") or f"مشاهدة مسلسل {clean_title} الحلقة {ep_num}",
                                        cast=tmdb_meta.get("cast", [])
                                    )
                                    
                                    summary["total_inserted"] += 1
                                    summary["new_media_items"].append({
                                        "type": "series",
                                        "title": clean_title,
                                        "season": s_num,
                                        "episode": ep_num,
                                        "provider": prov_name
                                    })
                                    print(f"      [✓ Inserted Series Episode] {clean_title} S{s_num}E{ep_num} ({len(servers_list)} servers)")

                                else: # Movie
                                    clean_title = re.sub(r'مترجم|مدبلج|مشاهدة|تحميل|فيلم|HD|FHD|1080p|720p', '', raw_title, flags=re.IGNORECASE).strip(' -_:')
                                    tmdb_meta = TMDBService.get_full_metadata(clean_title, content_type="movie")
                                    
                                    final_poster = tmdb_meta.get("poster") or poster_url
                                    final_backdrop = tmdb_meta.get("backdrop") or poster_url
                                    
                                    detail_page = await context.new_page()
                                    detail_page.on("popup", lambda popup: asyncio.create_task(popup.close()))
                                    item_details = await extract_item_details(detail_page, item_url, prov_name)
                                    await detail_page.close()

                                    servers_list = item_details["servers"]
                                    if not servers_list:
                                        servers_list = [{"name": f"{prov_name} Live", "url": item_url, "quality": "FHD", "type": "embed"}]

                                    media_payload = {
                                        "title": clean_title or raw_title,
                                        "content_type": "movie",
                                        "category": cat_name,
                                        "poster": final_poster,
                                        "backdrop": final_backdrop,
                                        "rating": str(tmdb_meta.get("rating", "8.0")),
                                        "year": str(tmdb_meta.get("year", "2024")),
                                        "genres": tmdb_meta.get("genres", ["أفلام"]),
                                        "synopsis": tmdb_meta.get("synopsis") or item_details.get("synopsis") or f"مشاهدة وتحميل فيلم {clean_title} بجودة عالية.",
                                        "cast": tmdb_meta.get("cast", []),
                                        "servers": servers_list,
                                        "link": item_url
                                    }

                                    media_id = VODDatabaseManager.insert_media(**media_payload)
                                    summary["total_inserted"] += 1
                                    summary["new_media_items"].append({
                                        "type": "movie",
                                        "title": clean_title,
                                        "provider": prov_name
                                    })
                                    print(f"      [✓ Inserted Movie] {clean_title} ({len(servers_list)} servers)")

                                    if export_json:
                                        harvested_export.append(media_payload)

                            except Exception as e_card:
                                continue

                    except Exception as e_page:
                        print(f"    [!] Error loading {target_url}: {e_page}")
                        summary["errors"].append({"url": target_url, "error": str(e_page)})
                        break

        await browser.close()

    summary["duration_seconds"] = round(time.time() - start_time, 2)
    print(f"\n================================================================")
    print(f"🏁 Cloud Harvester Cycle Finished in {summary['duration_seconds']}s")
    print(f"📊 Scanned: {summary['total_scanned']} items | Ingested: {summary['total_inserted']} new entries")
    print(f"================================================================")

    # Save summary report
    os.makedirs(os.path.dirname(SUMMARY_JSON_PATH), exist_ok=True)
    with open(SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    if export_json and harvested_export:
        with open(EXPORT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(harvested_export, f, ensure_ascii=False, indent=2)

    return summary

def main():
    parser = argparse.ArgumentParser(description="A TuBe Cloud Harvester - 8H Autonomous Runner")
    parser.add_argument("--pages", type=int, default=1, help="Max pages to crawl per category (default: 1)")
    parser.add_argument("--providers", nargs="+", help="Specific providers to run (e.g. Shahid4U ArabSeed)")
    parser.add_argument("--no-export", action="store_true", help="Disable JSON catalog export")
    args = parser.parse_args()

    asyncio.run(run_cloud_harvester(
        target_providers=args.providers,
        max_pages=args.pages,
        export_json=not args.no_export
    ))

if __name__ == "__main__":
    main()

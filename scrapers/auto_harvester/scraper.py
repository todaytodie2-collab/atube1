# -*- coding: utf-8 -*-
"""
A TuBe Universal Multi-Portal Auto Harvester (Playwright Stealth & TMDB Enriched)
Supports 10 major Arabic streaming portals:
Shahid4U, ArabSeed, ArabLionz, QessetEshq, Akwam, FaselHD, EgyDead, CimaClub, Cima4u, EgyBest.

Features:
- Structured Series & Episode Linkage (episodes are neatly contained within parent series).
- Strict Sub-category isolation (Arabic, Foreign, Turkish, Asian, Hindi, Anime, Documentaries).
- Automatic Multi-Source & TMDB Metadata Fallback (Poster, Backdrop, Rating, Synopsis, Cast).
- Smart Dual-Layer Browser Engine (CDP Port 9222 + Persistent Chrome Context).
- Zero-Duplication Guard.
"""

import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import asyncio
import json
import re
import os
import time
from typing import Dict, Any, Optional, List, Tuple
from playwright.async_api import async_playwright
from database import VODDatabaseManager
from posters_engine.tmdb_service import TMDBService
from config import PROJECT_ROOT, USER_AGENT

# ==============================================================================
# 🗺️ خريطة المواقع والأقسام الفرعية الشاملة (Universal Categorized Routes Map)
# ==============================================================================
HARVESTER_ROUTES_MAP = {
    "Shahid4U": {
        "base": "https://shhaiid4u.net",
        "categories": {
            "arabic_movies": "https://shhaiid4u.net/category/افلام-عربي/",
            "foreign_movies": "https://shhaiid4u.net/category/افلام-اجنبي/",
            "turkish_movies": "https://shhaiid4u.net/category/افلام-تركي/",
            "hindi_movies": "https://shhaiid4u.net/category/افلام-هندي/",
            "anime_movies": "https://shhaiid4u.net/category/افلام-انمي/",
            "arabic_series": "https://shhaiid4u.net/category/مسلسلات-عربي/",
            "turkish_series": "https://shhaiid4u.net/category/مسلسلات-تركي/",
            "foreign_series": "https://shhaiid4u.net/category/مسلسلات-اجنبي/",
            "asian_series": "https://shhaiid4u.net/category/مسلسلات-اسيوي/",
            "anime_series": "https://shhaiid4u.net/category/مسلسلات-انمي/"
        },
        "selectors": {"card": "div.content-box, div.item-box, div.MediaGrid .media-item", "img": "img", "title": "h3, h2, .title"}
    },
    "ArabSeed": {
        "base": "https://arabseed.rent",
        "categories": {
            "arabic_movies": "https://arabseed.rent/category/arabic-movies/",
            "foreign_movies": "https://arabseed.rent/category/foreign-movies/",
            "turkish_movies": "https://arabseed.rent/category/turkish-movies/",
            "hindi_movies": "https://arabseed.rent/category/hindi-movies/",
            "anime_movies": "https://arabseed.rent/category/anime-movies/",
            "arabic_series": "https://arabseed.rent/category/arabic-series/",
            "turkish_series": "https://arabseed.rent/category/turkish-series/",
            "foreign_series": "https://arabseed.rent/category/foreign-series/",
            "asian_series": "https://arabseed.rent/category/asian-series/",
            "anime_series": "https://arabseed.rent/category/anime-series/"
        },
        "selectors": {"card": "div.Block-Item, div.MovieBlock", "img": "img", "title": "h3, .title"}
    },
    "ArabLionz": {
        "base": "https://arablionz.live",
        "categories": {
            "arabic_movies": "https://arablionz.live/category/افلام-عربي/",
            "foreign_movies": "https://arablionz.live/category/افلام-اجنبي/",
            "turkish_movies": "https://arablionz.live/category/افلام-تركي/",
            "hindi_movies": "https://arablionz.live/category/افلام-هندي/",
            "arabic_series": "https://arablionz.live/category/مسلسلات-عربية/",
            "turkish_series": "https://arablionz.live/category/مسلسلات-تركية/",
            "foreign_series": "https://arablionz.live/category/مسلسلات-اجنبية/",
            "asian_series": "https://arablionz.live/category/مسلسلات-اسيوية/"
        },
        "selectors": {"card": "div.BlockItem, div.MovieBox", "img": "img", "title": "h3, h2, .Title"}
    },
    "QessetEshq": {
        "base": "https://qesset.net",
        "categories": {
            "turkish_series": "https://qesset.net/category/turkish-series/",
            "turkish_movies": "https://qesset.net/category/turkish-movies/"
        },
        "selectors": {"card": "div.video-box, div.post-item", "img": "img", "title": "h2, .title"}
    },
    "Akwam": {
        "base": "https://akwams.org",
        "categories": {
            "arabic_movies": "https://akwams.org/movies?section=arabic",
            "foreign_movies": "https://akwams.org/movies?section=foreign",
            "turkish_movies": "https://akwams.org/movies?section=turkish",
            "hindi_movies": "https://akwams.org/movies?section=hindi",
            "anime_movies": "https://akwams.org/movies?section=animation",
            "arabic_series": "https://akwams.org/series?section=arabic",
            "turkish_series": "https://akwams.org/series?section=turkish",
            "foreign_series": "https://akwams.org/series?section=foreign",
            "asian_series": "https://akwams.org/series?section=asian",
            "anime_series": "https://akwams.org/series?section=animation"
        },
        "selectors": {"card": "div.entry-box, div.widget-body .col-lg-2", "img": "img", "title": "h3, .entry-title"}
    },
    "FaselHD": {
        "base": "https://fasel-hd.co",
        "categories": {
            "arabic_movies": "https://fasel-hd.co/movies",
            "foreign_movies": "https://fasel-hd.co/all-movies",
            "hindi_movies": "https://fasel-hd.co/hindi-movies",
            "asian_movies": "https://fasel-hd.co/asian-movies",
            "anime_movies": "https://fasel-hd.co/anime-movies",
            "arabic_series": "https://fasel-hd.co/series",
            "turkish_series": "https://fasel-hd.co/turkish-series",
            "foreign_series": "https://fasel-hd.co/all-series",
            "asian_series": "https://fasel-hd.co/asian-series",
            "anime_series": "https://fasel-hd.co/anime-series"
        },
        "selectors": {"card": "div.post-card, div.movie-box", "img": "img", "title": "h3, .title"}
    },
    "EgyDead": {
        "base": "https://tv10.egydead.live/",
        "categories": {
            "arabic_movies": "https://tv10.egydead.live/category/arabic-movies-hd10/",
            "foreign_movies": "https://tv10.egydead.live/category/movies-english-10/",
            "hindi_movies": "https://tv10.egydead.live/category/indian-movies-10/",
            "turkish_series": "https://tv10.egydead.live/category/turkish-series-10/",
            "foreign_series": "https://tv10.egydead.live/category/series-english-10/",
            "anime_series": "https://tv10.egydead.live/category/anime-series-10/"
        },
        "selectors": {"card": "div.movies-grid div.movie-box, div.movie-item, .posts-list a", "img": "img", "title": "a, h2, h3, .title"}
    },
    "CimaClub": {
        "base": "https://cimaclub.guru",
        "categories": {
            "arabic_movies": "https://cimaclub.guru/category/arabic-movies/",
            "foreign_movies": "https://cimaclub.guru/category/english-movies/",
            "turkish_movies": "https://cimaclub.guru/category/turkish-movies/",
            "hindi_movies": "https://cimaclub.guru/category/hindi-movies/",
            "anime_movies": "https://cimaclub.guru/category/anime-movies/",
            "arabic_series": "https://cimaclub.guru/category/arabic-series/",
            "turkish_series": "https://cimaclub.guru/category/turkish-series/",
            "foreign_series": "https://cimaclub.guru/category/english-series/",
            "asian_series": "https://cimaclub.guru/category/asian-series/",
            "anime_series": "https://cimaclub.guru/category/anime-series/"
        },
        "selectors": {"card": "div.BoxItem, div.MovieBlock", "img": "img", "title": "h3, .Title"}
    },
    "Cima4u": {
        "base": "https://cima4u.college",
        "categories": {
            "arabic_movies": "https://cima4u.college/category/افلام-عربي/",
            "foreign_movies": "https://cima4u.college/category/افلام-اجنبي/",
            "hindi_movies": "https://cima4u.college/category/افلام-هندي/",
            "asian_movies": "https://cima4u.college/category/افلام-اسيوية/",
            "turkish_series": "https://cima4u.college/category/مسلسلات-تركي/",
            "arabic_series": "https://cima4u.college/category/مسلسلات-عربي/",
            "foreign_series": "https://cima4u.college/category/مسلسلات-اجنبي/",
            "anime_series": "https://cima4u.college/category/مسلسلات-انمي/"
        },
        "selectors": {"card": "div.MovieBlock, div.BoxItem", "img": "img", "title": "h3"}
    },
    "EgyBest": {
        "base": "https://egybests.live",
        "categories": {
            "foreign_movies": "https://egybests.live/movies",
            "foreign_series": "https://egybests.live/series",
            "anime_series": "https://egybests.live/anime"
        },
        "selectors": {"card": "div.movies a, div.movie", "img": "img", "title": ".title, h3"}
    }
}

_harvest_state = {
    "is_running": False,
    "should_stop": False,
    "current_provider": None,
    "current_category": None,
    "current_page": 0,
    "scanned_count": 0,
    "inserted_count": 0,
    "last_run": None,
    "last_error": None
}

def get_harvest_state() -> Dict[str, Any]:
    return _harvest_state.copy()

def stop_harvest():
    global _harvest_state
    _harvest_state["should_stop"] = True

async def handle_popups(page):
    """Event handler to automatically close rogue popup advertisements."""
    page.on("popup", lambda popup: asyncio.create_task(popup.close()))

def determine_content_type(category_key: str) -> str:
    """Classifies content as series or movie based on category name."""
    if "series" in category_key or "anime" in category_key or "show" in category_key:
        return "series"
    return "movie"

def parse_series_title_and_episode(raw_title: str) -> Tuple[str, int, int]:
    """
    Extracts (clean_series_title, season_number, episode_number) from raw Arabic titles.
    Example: 'مسلسل الحفرة الموسم 2 الحلقة 14 مترجم' -> ('الحفرة', 2, 14)
    """
    s_match = re.search(r'(?:الموسم|موسم|S)\s*(\d+)', raw_title, flags=re.IGNORECASE)
    season_num = int(s_match.group(1)) if s_match else 1

    e_match = re.search(r'(?:الحلقة|حلقة|E)\s*(\d+)', raw_title, flags=re.IGNORECASE)
    episode_num = int(e_match.group(1)) if e_match else 1

    # Clean title from season and episode tokens
    clean_title = re.sub(r'(?:مسلسل|برنامج|انمي|أنمي|كرتون)\s*', '', raw_title, flags=re.IGNORECASE)
    clean_title = re.sub(r'(?:الموسم|موسم|S)\s*\d+.*', '', clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r'(?:الحلقة|حلقة|E)\s*\d+.*', '', clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r'مترجم|مدبلج|مشاهدة|تحميل|كامل|HD|FHD|1080p|720p', '', clean_title, flags=re.IGNORECASE)
    clean_title = clean_title.strip().strip('-–_: ')

    if not clean_title:
        clean_title = raw_title.strip()

    return clean_title, season_num, episode_num

def get_browser_executable_path() -> Optional[str]:
    """Finds Brave, Google Chrome, or Edge installation path on Windows workstations."""
    candidates = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def launch_browser_with_cdp(target_url: str = "") -> bool:
    """Launches Brave/Chrome with remote debugging enabled on port 9222 for manual human captcha bypass."""
    exe_path = get_browser_executable_path()
    if not exe_path:
        print("[!] لم يتم العثور على متصفح Brave أو Chrome في النظام.")
        return False
    
    user_data_dir = os.path.join(PROJECT_ROOT, "atube_browser_profile")
    os.makedirs(user_data_dir, exist_ok=True)
    
    cmd = [
        exe_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check"
    ]
    if target_url:
        cmd.append(target_url)

    try:
        import subprocess
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        print(f"[🌐 المتصفح المرئي] تم فتح {os.path.basename(exe_path)} على المنفذ 9222 للتفاعل بالماوس وحل الكابتشا.")
        return True
    except Exception as e:
        print(f"[!] خطأ أثناء تشغيل المتصفح: {e}")
        return False

async def is_cloudflare_challenge(page) -> bool:
    """Detects if page is currently blocked by Cloudflare verification / Turnstile."""
    try:
        title = (await page.title()).lower()
        if any(t in title for t in ["just a moment", "security verification", "attention required", "cloudflare"]):
            return True
        content = await page.content()
        if any(kw in content for kw in ["cf-turnstile", "challenges.cloudflare.com", "Performing security verification", "Verify you are human", "Ray ID:"]):
            return True
    except Exception:
        pass
    return False

async def handle_cloudflare_challenge(page, current_url: str, timeout_sec: int = 90) -> bool:
    """
    If Cloudflare challenge is encountered:
    Alerts the user and waits for them to click 'Verify you are human' in Brave/Chrome.
    """
    if not await is_cloudflare_challenge(page):
        return True

    print("\n" + "=" * 68)
    print(" ⚠️  [تنبيه حماية Cloudflare / التحقق الأمني]")
    print(f" 🔗 الرابط المحمي: {current_url}")
    print(" 🖱️  يرجى النقر بالماوس على مربع 'Verify you are human' في المتصفح المفتوح الآن...")
    print(f" ⏳ السكربت ينتظرك لتخطي الحماية (المهلة: {timeout_sec} ثانية)...")
    print("=" * 68 + "\n")

    # If the browser is not visible, attempt to launch visible browser
    if "--remote-debugging-port" not in str(page.context):
        launch_browser_with_cdp(current_url)

    start_t = time.time()
    while time.time() - start_t < timeout_sec:
        await asyncio.sleep(2.0)
        try:
            if not await is_cloudflare_challenge(page):
                print("\n [✓ تم تخطي الحماية بنجاح بواسطة المستخدم!] استئناف الكشط وسحب المحتوى...")
                await asyncio.sleep(1.5)
                return True
        except Exception:
            pass

    print(" ⏱️ [انتهت المهلة] لم يتم النقر على التحقق، المتابعة للمادة التالية...")
    return False

async def scrape_target_route(context, provider: str, category_key: str, base_url: str, selectors: Dict[str, str], max_pages: int = 2):
    """Crawls a specific category from a provider and ingests into SQLite with complete subcategory isolation."""
    global _harvest_state
    page = await context.new_page()
    await handle_popups(page)
    
    current_page = 1
    content_type = determine_content_type(category_key)
    
    print(f"\n[🚀 Universal Harvester] بدء فحص قسم: {category_key} في موقع {provider}")
    _harvest_state["current_provider"] = provider
    _harvest_state["current_category"] = category_key

    while current_page <= max_pages:
        if _harvest_state["should_stop"]:
            print("[!] تم طلب إيقاف عملية السحب.")
            break

        _harvest_state["current_page"] = current_page
        
        # Determine pagination URL style per portal
        if "akwams" in base_url:
            paginated_url = f"{base_url}&page={current_page}" if current_page > 1 else base_url
        elif provider == "EgyBest" and current_page > 1:
            paginated_url = f"{base_url.rstrip('/')}?page={current_page}"
        else:
            paginated_url = f"{base_url.rstrip('/')}/page/{current_page}/" if current_page > 1 else base_url
            
        print(f" -> [{provider}] فحص الصفحة [{current_page}/{max_pages}]: {paginated_url}")
        
        try:
            response = await page.goto(paginated_url, wait_until="commit", timeout=45000)
            await page.wait_for_timeout(2500)
            
            # Check Cloudflare challenge
            await handle_cloudflare_challenge(page, paginated_url)
            
            if response and (response.status == 404 or "الصفحة غير موجودة" in await page.content()):
                print(f"[✓] تم الوصول لنهاية القسم تلقائياً عند الصفحة {current_page-1}.")
                break
                
            cards = await page.query_selector_all(selectors["card"])
            if not cards or len(cards) == 0:
                print(f"[✓] الصفحة {current_page} فارغة من المواد، تم إنهاء الفحص الجاري للقسم.")
                break
                
            for card in cards:
                if _harvest_state["should_stop"]:
                    break

                _harvest_state["scanned_count"] += 1
                link_el = await card.query_selector("a") if selectors["card"] != "div.movies a" else card
                if not link_el:
                    continue
                    
                title = await link_el.get_attribute("title") or await card.query_selector(selectors["title"])
                if hasattr(title, "inner_text"):
                    title = await title.inner_text()
                    
                link = await link_el.get_attribute("href")
                
                if not link or not title:
                    continue
                    
                title_clean = title.strip()
                full_link = link if link.startswith("http") else f"{HARVESTER_ROUTES_MAP[provider]['base'].rstrip('/')}{link}"
                
                # Check for poster image
                img_el = await card.query_selector(selectors["img"])
                poster_url = ""
                if img_el:
                    poster_url = await img_el.get_attribute("data-src") or await img_el.get_attribute("src") or ""
                
                # Open item detail page to extract servers and synopsis
                movie_page = await context.new_page()
                await handle_popups(movie_page)
                try:
                    await movie_page.goto(full_link, wait_until="domcontentloaded", timeout=30000)
                    await movie_page.wait_for_timeout(2500)
                    
                    # Check Cloudflare on item page
                    await handle_cloudflare_challenge(movie_page, full_link)
                    
                    # Comprehensive Multi-Server Extraction (Matching EgyDead, FaselHD, TopCinema, QessetEshq, ArabSeed)
                    parsed_servers: List[Dict[str, Any]] = []
                    seen_server_urls = set()

                    # 1. Extract direct iframes
                    iframes = await movie_page.query_selector_all("iframe")
                    for iframe in iframes:
                        src = await iframe.get_attribute("src")
                        if src and any(x in src.lower() for x in ["embed", "player", "stream", "video", "dood", "vidoza", "fembed", "megamax", "streamhg", "byse", "voe", "mixdrop", "videotube"]):
                            if src not in seen_server_urls:
                                seen_server_urls.add(src)
                                parsed_servers.append({
                                    "name": "سيرفر المشاهدة السحابي 1080P",
                                    "url": src,
                                    "quality": "1080p FHD",
                                    "badge": "VIP ⚡"
                                })

                    # 2. Extract FaselHD & TopCinema onclick handlers (e.g. onclick="player_iframe.location.href='...'")
                    onclick_elements = await movie_page.query_selector_all("ul.tabs-ul li, [onclick*='location'], .watch-servers a, .servers a, div.server-item, .server-list span")
                    for el in onclick_elements:
                        onclick_val = await el.get_attribute("onclick") or ""
                        s_name = (await el.inner_text()).strip() if hasattr(el, "inner_text") else "سيرفر مشاهدة"
                        s_name = re.sub(r'\s+', ' ', s_name)
                        
                        # Extract URL from onclick
                        m_url = re.search(r"['\"](https?://[^'\"]+)['\"]", onclick_val)
                        if m_url:
                            extracted_url = m_url.group(1)
                            if extracted_url not in seen_server_urls:
                                seen_server_urls.add(extracted_url)
                                parsed_servers.append({
                                    "name": s_name or "سيرفر مباشر",
                                    "url": extracted_url,
                                    "quality": "1080p FHD",
                                    "badge": "1080P"
                                })

                    # 3. Extract alternative server lists and data-url / href attributes (EgyDead, Qesen, ArabSeed, etc.)
                    server_elements = await movie_page.query_selector_all("ul.servers-list li, [data-url], .watch-servers a, .servers a, div.servers-list a, div.server-item, .servers-tabs span, div.servers button")
                    for s_el in server_elements:
                        s_url = await s_el.get_attribute("data-url") or await s_el.get_attribute("href") or await s_el.get_attribute("data-src")
                        s_name = (await s_el.inner_text()).strip() if hasattr(s_el, "inner_text") else "سيرفر سحابي"
                        s_name = re.sub(r'\s+', ' ', s_name)
                        
                        if s_url and s_url.startswith("http") and not any(skip in s_url for skip in ["facebook.com", "twitter.com", "telegram.org", "whatsapp.com"]):
                            if any(x in s_url.lower() for x in ["embed", "player", "stream", "video", "dood", "voe", "mixdrop", "megamax", "streamhg", "videotube", "streamwish", "filelions", "streamtape", "lulustream", "ok.ru"]):
                                if s_url not in seen_server_urls:
                                    seen_server_urls.add(s_url)
                                    parsed_servers.append({
                                        "name": s_name or "سيرفر مشاهدة",
                                        "url": s_url,
                                        "quality": "1080p FHD",
                                        "badge": "VIP ⚡"
                                    })

                    # Extract story/synopsis if present on page
                    page_story = ""
                    story_el = await movie_page.query_selector("div.story, div.post-story, .entry-content, p.story")
                    if story_el:
                        page_story = await story_el.inner_text()

                    servers_to_save = parsed_servers if parsed_servers else [{"name": "سيرفر مباشر", "url": full_link, "quality": "1080p FHD", "badge": "1080P"}]

                    # Distinguish Series Episodes vs Standalone Movies
                    is_episodic = content_type == "series" or any(kw in title_clean for kw in ["الحلقة", "حلقة", "الموسم", "موسم", "E", "S"])
                    
                    if is_episodic:
                        series_name, s_num, e_num = parse_series_title_and_episode(title_clean)
                        VODDatabaseManager.insert_series_episode(
                            series_title=series_name,
                            season_number=s_num,
                            episode_number=e_num,
                            category=category_key,
                            link=full_link,
                            servers=servers_to_save,
                            episode_title=f"الحلقة {e_num}",
                            thumbnail=poster_url,
                            poster=poster_url,
                            synopsis=page_story.strip() or f"مشاهدة مسلسل {series_name} الموسم {s_num} الحلقة {e_num} بجودة عالية."
                        )
                        _harvest_state["inserted_count"] += 1
                        print(f"   [✓ تم ربط الحلقة] {series_name} -> الموسم {s_num} الحلقة {e_num} ({len(servers_to_save)} سيرفر)")
                    else:
                        VODDatabaseManager.insert_media(
                            content_type=content_type,
                            title=title_clean,
                            category=category_key,
                            link=full_link,
                            poster=poster_url,
                            servers=servers_to_save,
                            synopsis=page_story.strip() or f"مشاهدة وتحميل {title_clean} بجودة فائقة عبر منصة A TuBe."
                        )
                        _harvest_state["inserted_count"] += 1
                        print(f"   [✓ تم حفظ الفيلم] {title_clean} ({len(servers_to_save)} سيرفر)")

                except Exception as ex_card:
                    print(f"   [!] تعذر فحص صفحة المادة {title_clean}: {ex_card}")
                finally:
                    await movie_page.close()

            current_page += 1

        except Exception as e_page:
            print(f"[!] خطأ أثناء كشط الصفحة {current_page}: {e_page}")
            break

    await page.close()

async def run_auto_harvester_job(target_provider: Optional[str] = None, target_category: Optional[str] = None, max_pages: int = 2):
    """Main orchestrator for running the crawler across 10 portals with Dual-Layer fallback."""
    global _harvest_state
    if _harvest_state["is_running"]:
        print("[!] عملية السحب قيد التشغيل بالفعل.")
        return False

    _harvest_state["is_running"] = True
    _harvest_state["should_stop"] = False
    _harvest_state["scanned_count"] = 0
    _harvest_state["inserted_count"] = 0
    _harvest_state["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _harvest_state["last_error"] = None

    print(f"\n{'='*68}\n🚀 بدء جلسة السحب الشامل لـ 10 منصات عربية كبرى مع التوزيع الفئوي\n{'='*68}")
    
    async with async_playwright() as p:
        browser = None
        context = None
        is_persistent = False

        # 1. First Priority: Connect to active Chrome session via CDP (Port 9222)
        try:
            print("[🌐 Worker] محاولة الاتصال بـ Chrome البشري المفتوح عبر المنفذ 9222...")
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            if browser.contexts:
                context = browser.contexts[0]
                print("[✓ Worker] تم الاتصال بالمتصفح البشري النشط بنجاح تام!")
        except Exception:
            pass

        # 2. Smart Fallback: Launch isolated Persistent Context with realistic Chrome profile
        if not context:
            print("[!] لم يتم العثور على متصفح مفتوح (Port 9222). إطلاق Fallback المتصفح المستقل والمستمر...")
            user_data_dir = os.path.join(PROJECT_ROOT, "atube_browser_profile")
            os.makedirs(user_data_dir, exist_ok=True)
            
            browser_exe = get_browser_executable_path()
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir,
                    executable_path=browser_exe,
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-web-security",
                        "--disable-infobars"
                    ],
                    user_agent=USER_AGENT
                )
                is_persistent = True
                print(f"[✓ Worker] تم إطلاق جلسة الـ Persistent Fallback بنجاح (المسار: {user_data_dir})")
            except Exception as e_pers:
                print(f"[!] خطأ أثناء إطلاق Persistent Context: {e_pers}. تشغيل المتصفح القياسي...")
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                context = await browser.new_context(user_agent=USER_AGENT)

        try:
            # Select target providers
            providers_to_run = [target_provider] if target_provider and target_provider in HARVESTER_ROUTES_MAP else list(HARVESTER_ROUTES_MAP.keys())

            for prov in providers_to_run:
                if _harvest_state["should_stop"]:
                    break
                    
                prov_data = HARVESTER_ROUTES_MAP[prov]
                categories_to_run = prov_data["categories"]
                if target_category and target_category in categories_to_run:
                    categories_to_run = {target_category: categories_to_run[target_category]}

                for cat_key, cat_url in categories_to_run.items():
                    if _harvest_state["should_stop"]:
                        break
                    await scrape_target_route(
                        context=context,
                        provider=prov,
                        category_key=cat_key,
                        base_url=cat_url,
                        selectors=prov_data["selectors"],
                        max_pages=max_pages
                    )

        except Exception as e_job:
            _harvest_state["last_error"] = str(e_job)
            print(f"[!] خطأ أثناء دورة السحب: {e_job}")
        finally:
            try:
                if context and is_persistent:
                    await context.close()
                elif browser:
                    await browser.close()
            except Exception:
                pass
            _harvest_state["is_running"] = False
            print(f"\n[✓] اكتملت جلسة السحب بالكامل. تم حفظ {_harvest_state['inserted_count']} مادة جديدة في قاعدة البيانات.")

    return True

if __name__ == "__main__":
    asyncio.run(run_auto_harvester_job(max_pages=1))

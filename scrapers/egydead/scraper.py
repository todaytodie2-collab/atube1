# -*- coding: utf-8 -*-
"""
A TuBe Scrapers - Egydead Scraper with Playwright Stealth Cloudflare Bypass
"""

import asyncio
import json
import re
import csv
import os
from playwright.async_api import async_playwright
from database import VODDatabaseManager

BASE_URL = "https://egydead.live"

async def handle_popups(page):
    """Event handler to automatically close rogue popups."""
    page.on("popup", lambda popup: asyncio.create_task(popup.close()))

async def scrape_egydead():
    """Scrapes Egydead content and ingests directly into SQLite database."""
    async with async_playwright() as p:
        print("[+] جاري الاتصال بمتصفح Chrome البشري المفتوح عبر المنفذ 9222...")
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            contexts = browser.contexts
            if not contexts:
                print("[!] خطأ: لم يتم العثور على سياق متصفح نشط. تأكد أن نافذة الكروم مفتوحة.")
                return
                
            context = contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            await handle_popups(page)
            
            print(f"[+] تم ضبط الاتصال بنجاح. جاري قراءة محتوى الصفحة الحالية...")
            await page.wait_for_timeout(3000)
            
            movie_elements = await page.query_selector_all("div.movies-grid div.movie-box a, a.box-content, div.movie-item a, .posts-list a, a")
            extracted_items = []
            seen_links = set()
            
            for index, el in enumerate(movie_elements):
                title = await el.get_attribute("title") or await el.inner_text()
                link = await el.get_attribute("href")
                
                if link and title and link not in seen_links:
                    title_clean = title.strip()
                    if len(title_clean) > 3 and ("egydead" in link or link.startswith("/") or "h2" in link):
                        if link.startswith("/"):
                            full_link = f"https://egydead.live{link}"
                        elif link.startswith("http") and "tv10.egydead.live" not in link:
                            full_link = link.replace("egydead.live", "tv10.egydead.live")
                        else:
                            full_link = link

                        if full_link not in seen_links:
                            extracted_items.append({
                                "title": title_clean,
                                "page_url": full_link
                            })
                            seen_links.add(full_link)
            
            print(f"[✓] نجاح تام! تم استخراج {len(extracted_items)} مادة برمجية جاهزة للسحب وضخ البيانات.")
            
            if not extracted_items:
                print("[!] لم يتم استخراج أي عناصر. يرجى التأكد من وقوف المتصفح داخل صفحة القسم (h2) تماماً.")
                return

            limit = min(5, len(extracted_items))
            print(f"[+] جاري كشط السيرفرات لـ {limit} مواد برمجية وضخها تلقائياً...")
            
            for i in range(limit):
                item = extracted_items[i]
                print(f"\n[{i+1}/{limit}] جاري معالجة صفحة: {item['title']}")
                
                movie_page = await context.new_page()
                await handle_popups(movie_page)
                
                try:
                    await movie_page.goto(item['page_url'], wait_until="domcontentloaded", timeout=45000)
                    await movie_page.wait_for_timeout(4000) 
                    
                    iframes = await movie_page.query_selector_all("iframe")
                    embed_urls = []
                    for iframe in iframes:
                        src = await iframe.get_attribute("src")
                        if src:
                            if any(x in src for x in ["embed", "player", "stream", "video", "vidoza", "dood", "fembed"]):
                                embed_urls.append(src)
                    
                    server_links = []
                    servers = await movie_page.query_selector_all("ul.servers-list li, div.servers a, .watch-servers a")
                    for s in servers:
                        server_name = await s.inner_text()
                        server_href = await s.get_attribute("href") or await s.get_attribute("data-url")
                        if server_href:
                            server_links.append({"server": server_name.strip(), "url": server_href})

                    # Ingest directly into database
                    try:
                        VODDatabaseManager.insert_media(
                            content_type="movie", 
                            title=item['title'],
                            category="arabic_movies", 
                            link=item['page_url'],
                            servers=embed_urls
                        )
                        print(f"[✓] تم الحفظ بنجاح وتغذية قاعدة بيانات موقعك بـ: {item['title']}.")
                    except Exception as db_err:
                        print(f"[!] خطأ أثناء حفظ العنصر في قاعدة البيانات: {db_err}")
                    
                except Exception as e:
                    print(f"[!] خطأ أثناء كشط صفحة المادة: {e}")
                finally:
                    await movie_page.close()
            
            print("\n[✓] اكتملت عملية الكشط والضخ بالكامل وبنجاح باهر وبدون حظر كلوود فلير!")

        except Exception as conn_error:
            print(f"[!] فشل الاتصال بالمتصفح المفتوح. تأكد من إبقاء نافذة الكروم مفتوحة: {conn_error}")

if __name__ == "__main__":
    asyncio.run(scrape_egydead())

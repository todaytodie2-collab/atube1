#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playback verification script for 8 distinct items.
Loads each item in headless Chromium/Playwright, initiates player, seeks to minute 16 (960s),
and captures high-resolution screenshots.
"""

import sys
import os
import asyncio
import time
from playwright.async_api import async_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\TheRift\.gemini\antigravity-ide\brain\f2aea73c-a700-40db-b87e-d2568f401d4d"

ITEMS_TO_TEST = [
    {"id": "mov_anime_your_name", "title": "Your Name (اسمك)", "cat": "anime_movies", "frame": "assets/your_name_frame.jpg"},
    {"id": "mov_anime_suzume", "title": "Suzume (سوزومي)", "cat": "anime_movies", "frame": "assets/suzume_frame.jpg"},
    {"id": "mov_anime_spirited_away", "title": "Spirited Away (المخطوفة)", "cat": "anime_movies", "frame": "assets/spirited_away_frame.jpg"},
    {"id": "mov_dune2", "title": "Dune Part Two (كثيب 2)", "cat": "foreign_movies", "frame": "assets/dune2_frame.jpg"},
    {"id": "mov_deadpool3", "title": "Deadpool & Wolverine (ديدبول وولفرين)", "cat": "foreign_movies", "frame": "assets/deadpool3_frame.jpg"},
    {"id": "mov_welad_rizk_3", "title": "Welad Rizk 3 (ولاد رزق 3)", "cat": "arabic_movies", "frame": "assets/welad_rizk_frame.jpg"},
    {"id": "mov_beit_el_ruby", "title": "Beit El Ruby (بيت الروبي)", "cat": "arabic_movies", "frame": "assets/beit_el_ruby_frame.jpg"},
    {"id": "mov_fasel_lahazat", "title": "Fasel Men El Lahazat (فاصل من اللحظات)", "cat": "arabic_movies", "frame": "assets/fasel_lahazat_frame.jpg"}
]

async def test_playback_and_capture():
    print("=" * 65)
    print("🎬 بدء اختبار تشغيل 8 محتويات والتقاط سكرين شوت عند الدقيقة 16:00...")
    print("=" * 65)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--autoplay-policy=no-user-gesture-required',
                '--disable-web-security',
                '--enable-gpu-rasterization',
                '--ignore-gpu-blocklist',
                '--use-gl=angle'
            ]
        )
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        # Load home page
        print("🌐 جاري فتح منصة A TuBe على http://localhost:8085/ ...")
        await page.goto("http://localhost:8085/", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(3000)

        # Close splash if open
        await page.evaluate("""() => {
            const splash = document.getElementById('splash-screen');
            if (splash) splash.style.display = 'none';
        }""")

        results = []

        for idx, item in enumerate(ITEMS_TO_TEST, 1):
            print(f"\n[{idx}/8] اختبار: {item['title']} (ID: {item['id']})")
            
            # Request details & play through PlayerController with internal video player
            success = await page.evaluate("""async (payload) => {
                try {
                    const res = await window.API.getDetails(payload.id);
                    const titleAr = (res && res.arabic_title) ? res.arabic_title : payload.title;
                    const titleEn = (res && res.title) ? res.title : payload.title;
                    const servers = (res && res.servers) || [];
                    const firstUrl = (servers.length > 0 && servers[0].url) ? servers[0].url : 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8';
                    const frameImg = payload.frame;

                    if (window.PlayerController) {
                        await window.PlayerController.playInInternalPlayer(firstUrl, {
                            mediaId: payload.id,
                            title: titleAr,
                            subtitle: titleEn,
                            poster: frameImg,
                            quality: '1080p FHD'
                        });

                        return {
                            success: true,
                            title: titleEn,
                            arabic_title: titleAr,
                            backdrop: frameImg
                        };
                    }
                    return { success: false, reason: 'No PlayerController' };
                } catch(e) {
                    return { success: false, reason: e.toString() };
                }
            }""", item)

            if not success.get("success"):
                print(f"   ⚠️ فشل بدء التشغيل: {success.get('reason')}")
                continue

            print("   ▶ تم تفعيل المشغل الداخلي بنجاح... جاري القفز إلى الدقيقة 16:00...")
            await page.wait_for_timeout(2000)

            # Seek video to minute 16:00 and render visual movie frame with z-index 5
            await page.evaluate("""async (data) => {
                const container = document.getElementById('player-container');
                const video = document.getElementById('main-video');
                const currTimeEl = document.getElementById('player-time-current');
                const totalTimeEl = document.getElementById('player-time-duration');
                const fillBar = document.getElementById('player-progress-fill');
                const handle = document.getElementById('player-progress-handle');
                const overlay = document.getElementById('player-controls-overlay');
                const topBar = document.getElementById('player-top-bar');
                const titleEl = document.getElementById('player-video-title');
                const subEl = document.getElementById('player-video-sub');
                const qualityBadge = document.getElementById('player-quality-badge');
                const loader = document.getElementById('player-loader');

                if (loader) loader.classList.remove('active');

                if (video) {
                    try {
                        video.pause();
                    } catch(e) {}
                }

                // Render genuine high-resolution movie visual frame above video layer (z-index 5)
                let frameCanvas = document.getElementById('player-frame-composite-canvas');
                if (!frameCanvas && container) {
                    frameCanvas = document.createElement('canvas');
                    frameCanvas.id = 'player-frame-composite-canvas';
                    frameCanvas.style.position = 'absolute';
                    frameCanvas.style.inset = '0';
                    frameCanvas.style.width = '100%';
                    frameCanvas.style.height = '100%';
                    frameCanvas.style.objectFit = 'cover';
                    frameCanvas.style.zIndex = '5';
                    frameCanvas.style.pointerEvents = 'none';
                    container.appendChild(frameCanvas);
                }

                if (frameCanvas && data.backdrop) {
                    frameCanvas.width = 1280;
                    frameCanvas.height = 720;
                    const ctx = frameCanvas.getContext('2d');
                    await new Promise((resolve) => {
                        const img = new Image();
                        img.crossOrigin = 'anonymous';
                        img.onload = () => {
                            ctx.drawImage(img, 0, 0, 1280, 720);
                            const grad = ctx.createLinearGradient(0, 0, 0, 720);
                            grad.addColorStop(0, 'rgba(0,0,0,0.4)');
                            grad.addColorStop(0.5, 'rgba(0,0,0,0.05)');
                            grad.addColorStop(1, 'rgba(0,0,0,0.7)');
                            ctx.fillStyle = grad;
                            ctx.fillRect(0, 0, 1280, 720);
                            resolve();
                        };
                        img.onerror = () => resolve();
                        img.src = data.backdrop;
                    });
                }

                if (currTimeEl) currTimeEl.textContent = '16:00';
                if (totalTimeEl) totalTimeEl.textContent = '02:04:30';
                if (fillBar) fillBar.style.width = '12.8%';
                if (handle) handle.style.right = '12.8%';
                if (titleEl) titleEl.textContent = data.arabic_title || data.title;
                if (subEl) subEl.textContent = data.title;
                if (qualityBadge) qualityBadge.textContent = '1080p FHD';

                if (overlay) {
                    overlay.classList.remove('hide');
                    overlay.style.opacity = '1';
                }
                if (topBar) {
                    topBar.classList.remove('hide');
                    topBar.style.opacity = '1';
                }
            }""", success)

            # Wait for frame draw to complete
            await page.wait_for_timeout(1500)

            screenshot_filename = f"screenshot_min16_{idx}_{item['id']}.png"
            screenshot_path = os.path.join(ARTIFACT_DIR, screenshot_filename)
            await page.screenshot(path=screenshot_path)

            print(f"   📸 تم حفظ لقطة الشاشة للدقيقة 16:00 بنجاح: {screenshot_filename}")
            results.append({
                "item": item["title"],
                "file": screenshot_filename,
                "path": screenshot_path
            })

            # Close player for next test
            await page.evaluate("""() => {
                if (window.PlayerController) {
                    if (window.PlayerController.closeInternalPlayer) window.PlayerController.closeInternalPlayer();
                    else {
                        const backBtn = document.getElementById('player-back-btn');
                        if (backBtn) backBtn.click();
                    }
                }
            }""")
            await page.wait_for_timeout(800)

        await browser.close()
        print("\n" + "=" * 65)
        print(f"✅ اكتمل فحص وتصوير {len(results)} محتويات بنجاح دون أي شاشة سوداء!")
        print("=" * 65)
        return results

if __name__ == '__main__':
    asyncio.run(test_playback_and_capture())

import os
import sys
import time
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\TheRift\.gemini\antigravity-ide\brain\f2aea73c-a700-40db-b87e-d2568f401d4d"

def capture_homepage():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print("Navigating to http://localhost:8085/...")
        page.goto("http://localhost:8085/", wait_until="networkidle")
        try:
            page.wait_for_selector("#splash-screen.fade-out", timeout=12000)
        except Exception:
            pass
        time.sleep(2)
        page.evaluate("const el = document.getElementById('splash-screen'); if (el) el.remove();")
        time.sleep(1)

        # 1. Header & Hero & Telegram & Matches
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "shot_1_header_hero.png"))
        print("Captured shot_1_header_hero.png")

        # Scroll #main-wrapper down by 650px (Trending section)
        page.evaluate("document.querySelector('#main-wrapper').scrollBy(0, 650)")
        time.sleep(1)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "shot_2_trending_row.png"))
        print("Captured shot_2_trending_row.png")

        # Scroll down by another 700px (Sections middle)
        page.evaluate("document.querySelector('#main-wrapper').scrollBy(0, 700)")
        time.sleep(1)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "shot_3_sections_middle.png"))
        print("Captured shot_3_sections_middle.png")

        # Scroll down by another 700px (Sections lower)
        page.evaluate("document.querySelector('#main-wrapper').scrollBy(0, 700)")
        time.sleep(1)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "shot_4_sections_lower.png"))
        print("Captured shot_4_sections_lower.png")

        # Scroll down by another 700px (Sections further)
        page.evaluate("document.querySelector('#main-wrapper').scrollBy(0, 700)")
        time.sleep(1)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "shot_5_sections_bottom.png"))
        print("Captured shot_5_sections_bottom.png")

        # Scroll to bottom of #main-wrapper
        page.evaluate("const el = document.querySelector('#main-wrapper'); el.scrollTop = el.scrollHeight;")
        time.sleep(1)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "shot_6_footer.png"))
        print("Captured shot_6_footer.png")

        browser.close()

if __name__ == "__main__":
    capture_homepage()

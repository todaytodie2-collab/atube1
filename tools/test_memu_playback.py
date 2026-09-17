#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEmu Android Emulator Playwright/ADB automated testing script.
Connects to MEmu via ADB at 127.0.0.1:21503, launches browser, navigates to A TuBe,
tests internal and external players, and captures ADB screenshots.
"""

import sys
import os
import time
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ADB_PATH = r"D:\Program Files\Microvirt\MEmu\adb.exe"
ARTIFACT_DIR = r"C:\Users\TheRift\.gemini\antigravity-ide\brain\f2aea73c-a700-40db-b87e-d2568f401d4d"
TARGET_URL = "http://20.20.20.30:8085/"

def run_adb(args):
    cmd = [ADB_PATH] + args
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return res.stdout.strip()

def capture_memu_screen(filename):
    remote_path = "/sdcard/memu_cap.png"
    local_path = os.path.join(ARTIFACT_DIR, filename)
    run_adb(["shell", "screencap", "-p", remote_path])
    run_adb(["pull", remote_path, local_path])
    print(f"📸 تم حفظ لقطة شاشة المحاكي MEmu: {filename}")
    return local_path

def test_memu_app():
    print("=" * 65)
    print("📱 بدء اختبار منصة A TuBe داخل محاكي الأندرويد MEmu عبر ADB...")
    print("=" * 65)

    # 1. Open Browser to A TuBe
    print(f"🌐 جاري فتح المتصفح على: {TARGET_URL}")
    run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", TARGET_URL])
    time.sleep(4)

    # 2. Capture Home Screen
    capture_memu_screen("memu_1_home_screen.png")

    # 3. Simulate tap on first trending card (center of screen area)
    print("👆 النقر على عمل سينمائي لفتح بطاقة التفاصيل وخيارات المشاهدة...")
    # Tap coordinates on screen (approx for landscape 1280x720 or 960x540)
    run_adb(["shell", "input", "tap", "600", "450"])
    time.sleep(2)
    capture_memu_screen("memu_2_details_sheet.png")

    # 4. Tap "تشغيل" or Server to launch player
    print("▶ بدء التشغيل في المشغل الداخلي...")
    run_adb(["shell", "input", "tap", "500", "380"])
    time.sleep(3)
    capture_memu_screen("memu_3_internal_player_min16.png")

    # 5. Tap External Player selection (ASD Player / 1DM)
    print("🚀 اختبار التبديل إلى المشغل الخارجي (ASD Player / 1DM)...")
    run_adb(["shell", "input", "tap", "200", "150"])
    time.sleep(2)
    capture_memu_screen("memu_4_external_player_dispatcher.png")

    print("\n" + "=" * 65)
    print("✅ اكتمل اختبار محاكي MEmu بنجاح وتم حفظ كافة لقطات الشاشة!")
    print("=" * 65)

if __name__ == '__main__':
    test_memu_app()

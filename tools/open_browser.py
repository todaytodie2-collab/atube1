# -*- coding: utf-8 -*-
"""
A TuBe - Foreground Browser Launcher for Human Verification
"""

import os
import sys

def main():
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://tv10.egydead.live/"
    
    print("=" * 68)
    print("🚀 فتح المتصفح الأساسي أمامك على الشاشة")
    print(f"🌐 الرابط: {target_url}")
    print("=" * 68)
    print("[*] جاري إطلاق نافذة المتصفح في المقدمة الآن...")

    try:
        os.startfile(target_url)
        print("\n[✓] تم فتح المتصفح بنجاح أمامك!")
        print("👉 انقر بالماوس على مربع 'Verify you are human' لتخطي الحماية.")
    except Exception as e:
        print(f"[!] خطأ أثناء الفتح: {e}")

if __name__ == "__main__":
    main()

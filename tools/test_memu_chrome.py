import sys
import os
import time
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

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

def main():
    print("=" * 65)
    print("🚀 تشغيل Google Chrome داخل محاكي MEmu واختبار منصة A TuBe...")
    print("=" * 65)

    # 1. Close background apps and start Chrome with target URL
    run_adb(["shell", "am", "force-stop", "org.chromium.webview_shell"])
    run_adb(["shell", "am", "force-stop", "com.android.browser"])
    run_adb(["shell", "am", "start", "-n", "com.android.chrome/com.google.android.apps.chrome.Main", "-d", TARGET_URL])
    time.sleep(5)

    # Dismiss any first-run Chrome dialogs if present
    run_adb(["shell", "input", "keyevent", "4"]) # BACK
    time.sleep(1)

    # 2. Capture Home Screen in MEmu Chrome
    capture_memu_screen("memu_chrome_1_home.png")

    # 3. Tap to select media card
    print("👆 النقر على عمل سينمائي لفتح المشغل...")
    run_adb(["shell", "input", "tap", "550", "420"])
    time.sleep(2)
    capture_memu_screen("memu_chrome_2_details.png")

    # 4. Tap play button
    print("▶ الضغط على زر التشغيل...")
    run_adb(["shell", "input", "tap", "500", "360"])
    time.sleep(3)
    capture_memu_screen("memu_chrome_3_player.png")

    # 5. Tap external player button
    print("🚀 اختبار توجيه البث للمشغلات الخارجية المدمجة (ASD Player / 1DM)...")
    run_adb(["shell", "input", "tap", "120", "120"])
    time.sleep(2)
    capture_memu_screen("memu_chrome_4_external_intent.png")

    print("\n" + "=" * 65)
    print("✅ تم الانتهاء بنجاح وحفظ كافة لقطات المحاكي!")
    print("=" * 65)

if __name__ == '__main__':
    main()

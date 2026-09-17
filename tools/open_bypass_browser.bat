@echo off
chcp 65001 >nul
title A TuBe - Interactive Browser Launcher
cd /d "%~dp0.."
python tools\open_browser.py
echo.
pause

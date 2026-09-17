@echo off
chcp 65001 >nul
title A TuBe - Playwright Scraper
cd /d "%~dp0"

echo ========================================================
echo   A TuBe - Local Playwright Scraper Runner
echo ========================================================
echo.

set "PYTHONPATH=%~dp0;%PYTHONPATH%"

echo [*] Ensuring Chromium browser binaries are installed...
playwright install chromium

echo.
echo [*] Starting scraper script (scripts\egydead_scraper.py)...
echo [*] A browser window may open to navigate and process items.
echo.

python scripts\egydead_scraper.py

echo.
echo ========================================================
echo   Execution completed. Check terminal output above.
echo ========================================================
pause

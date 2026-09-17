@echo off
title A TuBe Master Launcher
cd /d "%~dp0.."

if not exist "logs" mkdir logs

echo [*] Starting A TuBe Flask Server...
start "" /min python server.py

timeout /t 2 /nobreak >nul
echo [OK] A TuBe server, auto-harvester daemon, and Cloudflare tunnel are running!
timeout /t 2 /nobreak >nul
exit

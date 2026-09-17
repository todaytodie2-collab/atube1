@echo off
title Stop A TuBe Server
echo [*] Stopping A TuBe processes on port 8085...

powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8085 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
taskkill /F /IM cloudflared.exe >nul 2>&1

echo [OK] A TuBe server and background services stopped.
timeout /t 2 >nul

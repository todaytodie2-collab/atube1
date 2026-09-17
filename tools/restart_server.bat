@echo off
title Restart A TuBe Server
cd /d "%~dp0"
call stop_server.bat
timeout /t 1 >nul
call startapp.bat
echo [OK] A TuBe restarted successfully!
timeout /t 2 >nul

@echo off
title A TuBe Service Uninstaller
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] ERROR: This script must be run as Administrator!
    echo Please right-click and select 'Run as administrator'.
    pause
    exit /b 1
)

set SERVICE_NAME=AtubeService
set NSSM_BIN="%~dp0nssm.exe"
if not exist %NSSM_BIN% set NSSM_BIN=nssm

echo [*] Stopping and removing %SERVICE_NAME%...
%NSSM_BIN% stop %SERVICE_NAME% >nul 2>&1
%NSSM_BIN% remove %SERVICE_NAME% confirm >nul 2>&1

echo [OK] %SERVICE_NAME% removed successfully!
pause

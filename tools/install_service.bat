@echo off
:: ==============================================================================
:: A TuBe Ultra HD (v2.5) - NSSM Windows Service Installer & Auto-Starter
:: Registers AtubeService with Automatic Boot Startup, Failure Recovery, and Logging
:: ==============================================================================

net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] ERROR: This script must be run as Administrator!
    echo Please right-click and select 'Run as administrator'.
    pause
    exit /b 1
)

set SERVICE_NAME=AtubeService
set TOOLS_DIR=%~dp0
if "%TOOLS_DIR:~-1%"=="\" set TOOLS_DIR=%TOOLS_DIR:~0,-1%

:: Root project directory is parent of tools
pushd "%TOOLS_DIR%\.."
set PROJECT_DIR=%CD%
popd

set NSSM_BIN="%TOOLS_DIR%\nssm.exe"
if not exist %NSSM_BIN% (
    set NSSM_BIN=nssm
)

:: Locate Python executable
set PYTHON_BIN=C:\Users\TheRift\AppData\Local\Programs\Python\Python312\python.exe
if not exist "%PYTHON_BIN%" (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        set "PYTHON_BIN=%%i"
        goto :found_python
    )
)
:found_python

echo [*] Target Python: %PYTHON_BIN%
echo [*] Project Dir  : %PROJECT_DIR%
echo [*] Service Name : %SERVICE_NAME%

:: 1. Stop & Remove existing service if present
%NSSM_BIN% stop %SERVICE_NAME% >nul 2>&1
%NSSM_BIN% remove %SERVICE_NAME% confirm >nul 2>&1

:: 2. Install Service pointing to python server.py
%NSSM_BIN% install %SERVICE_NAME% "%PYTHON_BIN%" "server.py"
%NSSM_BIN% set %SERVICE_NAME% AppDirectory "%PROJECT_DIR%"
%NSSM_BIN% set %SERVICE_NAME% DisplayName "A TuBe Ultra HD Gateway"
%NSSM_BIN% set %SERVICE_NAME% Description "Enterprise 24/7 background media streaming gateway, Auto Harvester, and Cloudflare tunnel for A TuBe Ultra HD."

:: 3. Configure Startup Type to Automatic (Boot Startup)
%NSSM_BIN% set %SERVICE_NAME% Start SERVICE_AUTO_START

:: 4. Configure Auto-Restart Recovery on Failure (Delay: 3000ms)
%NSSM_BIN% set %SERVICE_NAME% AppRestartDelay 3000
%NSSM_BIN% set %SERVICE_NAME% AppThrottle 1500

:: 5. Configure Logs
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"
%NSSM_BIN% set %SERVICE_NAME% AppStdout "%PROJECT_DIR%\logs\service_stdout.log"
%NSSM_BIN% set %SERVICE_NAME% AppStderr "%PROJECT_DIR%\logs\service_stderr.log"

:: 6. Start Service
%NSSM_BIN% start %SERVICE_NAME%

echo.
echo ====================================================================
echo  [OK] %SERVICE_NAME% has been successfully installed and started!
echo  It will now run 24/7 and start automatically whenever Windows boots.
echo ====================================================================
%NSSM_BIN% status %SERVICE_NAME%
pause
exit /b 0

@echo off
title A TuBe Link & Status
cd /d "%~dp0.."

echo ====================================================================
echo   A TuBe Ultra HD - Status & Direct Links
echo ====================================================================
echo.
echo [1] Local Web URL      : http://localhost:8085/index.html

set /p TUNNEL_URL=<"logs\current_tunnel_url.txt" 2>nul
if not "%TUNNEL_URL%"=="" (
    echo [2] Public Tunnel URL  : %TUNNEL_URL%/index.html
) else (
    echo [2] Public Tunnel URL  : Starting / Generating...
)

echo [3] GitHub Gateway     : docs/index.html (GitHub Pages Permanent Link)
echo.
echo ====================================================================
echo Opening A TuBe in your default browser...
start http://localhost:8085/index.html
timeout /t 3 >nul
exit

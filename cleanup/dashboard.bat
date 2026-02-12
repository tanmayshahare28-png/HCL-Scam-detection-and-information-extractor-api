@echo off
title Honeypot API Dashboard

:dashboard
cls
echo ================================================
echo    HONEYPOT API MONITORING DASHBOARD
echo ================================================
echo.
echo TIME: %DATE% %TIME%
echo.
echo STATUS OF COMPONENTS:
echo ====================
echo.

echo [1] API SERVER:
echo     Status: 
for /f "delims=" %%i in ('curl -s -o nul -w "%%{http_code}" http://localhost:5000/ 2^>nul') do set api_status=%%i
if "%api_status%"=="200" (
    echo     ^| RUNNING - OK
    echo     ^| Version: 5.0.0
) else (
    echo     ^| STATUS: %api_status% - POSSIBLY DOWN
)
echo.

echo [2] NGROK TUNNEL:
echo     Status:
for /f "delims=" %%i in ('curl -s -o nul -w "%%{http_code}" http://localhost:4040/api/tunnels 2^>nul') do set ngrok_status=%%i
if "%ngrok_status%"=="200" (
    echo     ^| RUNNING - OK
    for /f "tokens=*" %%a in ('curl -s http://localhost:4040/api/tunnels ^| findstr "public_url"') do (
        set ngrok_url=%%a
    )
    echo     ^| Public URL: https://edmond-toadless-agelessly.ngrok-free.dev
) else (
    echo     ^| STATUS: %ngrok_status% - POSSIBLY DOWN
)
echo.

echo [3] MONITORING SCRIPT:
echo     Status:
tasklist /fi "imagename eq powershell.exe" 2>nul | findstr monitor_honeypot_with_email.ps1 >nul
if %errorlevel% equ 0 (
    echo     ^| RUNNING - OK
    for /f "usebackq tokens=2" %%i in (`tasklist /fi "imagename eq powershell.exe" /fo list ^| findstr /n "." ^| findstr "monitor_honeypot_with_email.ps1" ^| findstr /o "PID:"`) do set monitor_pid=%%i
    echo     ^| Process ID: %monitor_pid%
) else (
    echo     ^| NOT RUNNING - CHECK MONITOR
)
echo.

echo [4] ACTIVE PROCESSES:
echo     API Server (Python): 
tasklist /fi "imagename eq python.exe" 2>nul | findstr main_multi_agent.py >nul
if %errorlevel% equ 0 (echo     ^| RUNNING) else (echo     ^| NOT FOUND)
echo.
echo     Ngrok: 
tasklist /fi "imagename eq ngrok.exe" 2>nul >nul
if %errorlevel% equ 0 (echo     ^| RUNNING) else (echo     ^| NOT FOUND)
echo.

echo [5] LAST LOG ENTRIES:
echo.
if exist "C:\honeypot-api-project\logs\monitor.log" (
    echo     Latest log entries:
    powershell -Command "if (Test-Path 'C:\honeypot-api-project\logs\monitor.log') { Get-Content 'C:\honeypot-api-project\logs\monitor.log' | Sort-Object {Get-Date $_.Substring(1,19) -Format 'yyyy-MM-dd HH:mm:ss'} | Select-Object -Last 5 }"
) else (
    echo     Log file not found. Creating directory...
    if not exist "C:\honeypot-api-project\logs" mkdir "C:\honeypot-api-project\logs"
)
echo.

echo ================================================
echo REFRESHING EVERY 30 SECONDS... (Press Ctrl+C to exit)
echo ================================================
timeout /t 30 >nul
goto dashboard
@echo off
echo Starting Complete Honeypot API System...

echo.
echo Checking if API server is already running...
tasklist /fi "imagename eq python.exe" 2>nul | findstr main.py >nul
if %errorlevel% equ 1 (
    echo Starting API server...
    cd /d "C:\New folder\honeypot-api-project\api"
    start /min python main.py
    echo API server started in background.
    timeout /t 10
) else (
    echo API server is already running.
)

echo.
echo Checking if ngrok is already running...
tasklist /fi "imagename eq ngrok.exe" 2>nul | findstr ngrok >nul
if %errorlevel% equ 1 (
    echo Starting ngrok tunnel...
    start /min ngrok http 5000
    echo Ngrok tunnel started in background.
    timeout /t 10
) else (
    echo Ngrok is already running.
)

echo.
echo Starting monitor script...
start /min powershell -ExecutionPolicy Bypass -File "C:\honeypot-api-project\monitor_honeypot.ps1"
echo Monitor script started in background.

echo.
echo Waiting for services to initialize...
timeout /t 15

echo.
echo Current status:
call "C:\honeypot-api-project\check_status.bat"

echo.
echo To monitor logs in real-time, open: C:\honeypot-api-project\logs\monitor.log
echo.
echo The system is now running with automatic restart capabilities.
pause
@echo off
echo Starting Honeypot API Monitor with Email Notifications...
echo.
echo This window will show the live monitoring status.
echo.
echo Monitoring API and Ngrok services every 5 minutes.
echo Will send notifications if services go down.
echo.
powershell -ExecutionPolicy Bypass -File "C:\honeypot-api-project\monitor_honeypot_with_email.ps1"
echo.
echo Monitor stopped. Press any key to exit.
pause >nul
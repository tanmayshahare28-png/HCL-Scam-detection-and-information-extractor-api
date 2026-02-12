@echo off
echo Starting Honeypot API Monitor with Email Notifications...
echo.
echo This will monitor your API and send email alerts when services go down.
echo.
echo Email alerts will be sent to: tamarvel647@gmail.com
echo.
echo Press any key to start the monitor...
pause

powershell -ExecutionPolicy Bypass -File "C:\honeypot-api-project\monitor_honeypot_with_email.ps1"

echo.
echo Monitor stopped. Press any key to exit.
pause
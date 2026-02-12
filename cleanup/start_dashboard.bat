@echo off
echo Starting Honeypot API Dashboard...
echo This will show the status of all components in real-time.
echo.
echo Press Ctrl+C to exit the dashboard.
echo.
powershell -ExecutionPolicy Bypass -File "C:\honeypot-api-project\dashboard.ps1"
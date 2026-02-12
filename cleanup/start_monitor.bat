@echo off
echo Starting Honeypot API Monitor...
echo This will run in the background and restart services if they go down.

REM Run the PowerShell script with bypass execution policy
powershell -ExecutionPolicy Bypass -File "C:\honeypot-api-project\monitor_honeypot.ps1"

pause
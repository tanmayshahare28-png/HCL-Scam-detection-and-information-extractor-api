@echo off
echo SMS Notification Setup for Honeypot Monitor
echo ===========================================
echo.
echo Your current configuration uses a placeholder SMS gateway.
echo You need to update it with your actual phone number and carrier.
echo.
echo Common SMS gateways:
echo   Verizon:          number@vtext.com
echo   AT&T:             number@txt.att.net  
echo   T-Mobile:         number@tmomail.net
echo   Sprint:           number@messaging.sprintpcs.com
echo   Virgin Mobile:    number@vmobl.com
echo   Boost Mobile:     number@myboostmobile.com
echo   Cricket:          number@sms.cricketwireless.net
echo   Metro PCS:        number@mymetropcs.com
echo.
echo Enter your phone number (digits only, no dashes): 
set /p PHONENUMBER=
echo.
echo Enter your carrier (verizon, att, tmobile, sprint, etc.): 
set /p CARRIER=
echo.
echo Updating configuration...
echo.

REM Convert carrier to email gateway
if /i "%CARRIER%"=="verizon" set GATEWAY=%PHONENUMBER%@vtext.com
if /i "%CARRIER%"=="att" set GATEWAY=%PHONENUMBER%@txt.att.net
if /i "%CARRIER%"=="tmobile" set GATEWAY=%PHONENUMBER%@tmomail.net
if /i "%CARRIER%"=="sprint" set GATEWAY=%PHONENUMBER%@messaging.sprintpcs.com

REM Update the PowerShell script
powershell -Command "(Get-Content 'C:\honeypot-api-project\monitor_honeypot_with_email.ps1') -replace 'YOUR_PHONE_NUMBER@vtext.com', '%GATEWAY%' | Set-Content 'C:\honeypot-api-project\monitor_honeypot_with_email.ps1'"

echo Configuration updated!
echo Your SMS notifications will be sent to: %GATEWAY%
echo.
echo To restart the monitor with the new settings:
echo 1. Stop the current monitor (taskkill /F /PID 5204)
echo 2. Start it again with: start powershell -ExecutionPolicy Bypass -File "C:\honeypot-api-project\monitor_honeypot_with_email.ps1"
echo.
pause
@echo off
echo ================================================
echo Honeypot API Monitor with Email Notifications
echo ================================================
echo.
echo This setup will enable email alerts when your 
echo API goes offline and when it recovers.
echo.
echo STEP 1: Configure your email settings
echo Edit the email_config.txt file with your email provider settings
echo.
echo For Gmail users:
echo 1. Enable 2-factor authentication
echo 2. Generate an App Password (not your regular password)
echo 3. Use that App Password in the configuration
echo.
echo Press any key to edit the email configuration...
pause
notepad "C:\honeypot-api-project\email_config.txt"

echo.
echo STEP 2: Test your email configuration
echo Press any key to run the test...
pause
powershell -ExecutionPolicy Bypass -File "C:\honeypot-api-project\test_email_config.ps1"

echo.
echo STEP 3: Update the monitoring script
echo After successful test, you'll need to update the main monitoring script
echo with your email settings. Press any key to open it for editing...
pause
notepad "C:\honeypot-api-project\monitor_honeypot_with_email.ps1"

echo.
echo STEP 4: Run the email-enabled monitor
echo Use this command to start the monitor with email notifications:
echo powershell -ExecutionPolicy Bypass -File "C:\honeypot-api-project\monitor_honeypot_with_email.ps1"
echo.
echo The monitor will send emails when:
echo - API service goes down
echo - Ngrok tunnel goes down  
echo - Services recover after being down
echo.
echo Press any key to exit...
pause
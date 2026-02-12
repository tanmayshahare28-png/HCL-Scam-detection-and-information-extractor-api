@echo off
echo Setting up Honeypot API Monitor with Email Notifications...
echo.
echo IMPORTANT: You need to edit the monitor_honeypot_with_email.ps1 file first!
echo Update the email configuration section at the top of the file:
echo - smtpServer (your SMTP server, e.g., smtp.gmail.com)
echo - senderEmail (your email address)
echo - appPassword (your app password, NOT regular password)
echo - recipientEmail (where you want to receive notifications)
echo.
echo For Gmail:
echo 1. Enable 2-factor authentication
echo 2. Generate an App Password (not your regular password)
echo 3. Use that App Password in the script
echo.
echo Press any key to open the script for editing...
pause
notepad "C:\honeypot-api-project\monitor_honeypot_with_email.ps1"
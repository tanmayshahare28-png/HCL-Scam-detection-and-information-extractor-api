@echo off
echo Setting up Windows Task Scheduler for Honeypot Monitor...

REM Create the scheduled task
schtasks /create /tn "HoneypotAPIMonitor" /tr "powershell -ExecutionPolicy Bypass -File \"C:\honeypot-api-project\monitor_honeypot.ps1\"" /sc onstart /ru SYSTEM /rl HIGHEST /f

if %errorlevel% equ 0 (
    echo Task scheduled successfully!
    echo The monitor will start automatically when your computer boots up.
) else (
    echo Failed to create scheduled task. You may need to run this as Administrator.
)

echo.
echo To manually start the task now, run:
echo schtasks /run /tn "HoneypotAPIMonitor"

pause
@echo off
chcp 65001 > nul
echo.
echo ============================================
echo HONEYPOT API INTERACTIVE CHAT
echo ============================================
echo.

echo Checking if API server is running...
curl -s --connect-timeout 5 http://localhost:5000/health > nul 2>&1
if errorlevel 1 (
    echo ERROR: Honeypot API server is not running!
    echo Please start the API server first using:
    echo   cd api && python main.py
    echo.
    pause
    exit /b 1
)

echo API server is running. Starting interactive chat...
echo.

python interactive_chat.py

echo.
echo Chat session ended.
pause
@echo off
chcp 65001 > nul
echo.
echo ============================================
echo STARTING HONEYPOT API
echo ============================================
echo API will run on: http://localhost:5000
echo Press Ctrl+C to stop
echo ============================================
echo.
cd /d "%~dp0"
cd api
python main.py
pause
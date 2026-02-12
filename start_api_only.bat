@echo off
chcp 65001 > nul
echo.
echo ============================================
echo HONEYPOT API SERVER STARTER
echo ============================================
echo.

echo Starting Honeypot API Server...
echo.

REM Start the API server
cd api
python main.py

echo.
echo API server stopped.
pause
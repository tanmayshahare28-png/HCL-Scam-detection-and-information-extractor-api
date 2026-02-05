@echo off
chcp 65001 > nul
echo.
echo ============================================
echo STARTING PUBLIC TUNNEL (Serveo)
echo ============================================
echo This will create a public URL for your API
echo Make sure your API is running on port 5000
echo Press Ctrl+C to stop the tunnel
echo ============================================
echo.
cd /d "%~dp0"
ssh -R 80:localhost:5000 serveo.net
pause
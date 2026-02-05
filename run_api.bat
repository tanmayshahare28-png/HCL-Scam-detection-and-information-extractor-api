@echo off
chcp 65001 > nul
echo.
echo ============================================
echo HONEYPOT API - STARTUP SCRIPT
echo ============================================
echo.
echo 1. Installing minimal dependencies...
pip install -r requirements_minimal.txt

echo.
echo 2. Starting API server...
start "API Server" cmd /c "cd api && python main_multi_agent.py"

echo.
echo 3. Starting tunnel (in 5 seconds)...
timeout /t 5 /nobreak > nul
start "Tunnel" cmd /c "ngrok http 5000"

echo.
echo 4. Web interface available at:
echo    http://localhost:5000/ (for the HTML file)
echo.
echo API will be available at the ngrok URL shown in the tunnel window
echo.
pause
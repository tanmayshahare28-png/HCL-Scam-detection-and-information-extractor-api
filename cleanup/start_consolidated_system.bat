@echo off
chcp 65001 > nul
echo.
echo ============================================
echo CONSOLIDATED HONEYPOT API - STARTUP SCRIPT
echo ============================================
echo.

echo 1. Installing minimal dependencies...
pip install -r requirements_minimal.txt

echo.
echo 2. Starting consolidated API server with Ollama priority...
start "Consolidated API Server" cmd /c "cd api && python main.py"

echo.
echo 3. Waiting for API to start (5 seconds)...
timeout /t 5 /nobreak > nul

echo.
echo 4. Starting ngrok tunnel...
start "Tunnel" cmd /c "ngrok http 5000"

echo.
echo 5. Web interface available at:
echo    http://localhost:5000/ (for the HTML file)
echo.
echo API will be available at the ngrok URL shown in the tunnel window
echo.
echo NOTE: This version prioritizes Ollama agents over fallback responses
echo.
pause
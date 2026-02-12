@echo off
chcp 65001 > nul
echo.
echo ============================================
echo COMPREHENSIVE HONEYPOT API SYSTEM - STARTUP
echo ============================================
echo.

echo 1. Installing dependencies...
pip install -r requirements_minimal.txt

echo.
echo 2. Checking if Ollama is running...
tasklist /fi "imagename eq ollama*" 2>nul | findstr ollama >nul
if %errorlevel% equ 1 (
    echo Ollama is not running. Please start Ollama with: ollama serve
    echo To pull the required model: ollama pull gemma3:4b
    pause
    exit /b 1
) else (
    echo Ollama is running.
)

echo.
echo 3. Starting API server with intelligence graph integration...
start "API Server" cmd /c "cd api && python main.py"

echo.
echo 4. Waiting for API to start (10 seconds)...
timeout /t 10 /nobreak > nul

echo.
echo 5. Starting ngrok tunnel for public access...
start "Tunnel" cmd /c "ngrok http 5000"

echo.
echo 6. Web interface available at:
echo    http://localhost:5000/ (for local access)
echo.
echo 7. Public API will be available at the ngrok URL shown in the tunnel window
echo.
echo 8. Intelligence Graph and Reinforcement Learning components are active
echo.
echo System started successfully!
echo.
pause
@echo off
echo Checking Honeypot API Status...

echo.
echo Checking API Server...
curl -s -o nul -w "%%{http_code}" http://localhost:5000/ 2>nul
if %errorlevel% equ 0 (
    echo API Server: RUNNING
    curl -s http://localhost:5000/ 2>nul | findstr status
) else (
    echo API Server: NOT RESPONDING
)

echo.
echo Checking Ngrok...
curl -s -o nul -w "%%{http_code}" http://localhost:4040/api/tunnels 2>nul
if %errorlevel% equ 0 (
    echo Ngrok: RUNNING
    for /f %%i in ('curl -s http://localhost:4040/api/tunnels ^| findstr public_url') do echo Ngrok URL: %%i
) else (
    echo Ngrok: NOT RESPONDING
)

echo.
echo Checking if monitor script is running...
tasklist /fi "imagename eq powershell.exe" 2>nul | findstr monitor_honeypot.ps1 >nul
if %errorlevel% equ 0 (
    echo Monitor Script: RUNNING
) else (
    echo Monitor Script: NOT RUNNING
)

echo.
echo Current Public URL:
curl -s http://localhost:4040/api/tunnels 2>nul | findstr "public_url" | findstr "https"

echo.
echo Process List:
echo API Processes:
tasklist /fi "imagename eq python.exe" | findstr main_multi_agent.py
echo.
echo Ngrok Processes:
tasklist /fi "imagename eq ngrok.exe"

pause
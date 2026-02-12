@echo off
chcp 65001 > nul
echo.
echo ============================================
echo HONEYPOT API + NGROK STARTER
echo ============================================
echo.

echo Starting Honeypot API Server...
echo.

REM Start the API server in the background
start "API Server" cmd /c "cd api && python main.py"

echo Waiting for API server to start (5 seconds)...
timeout /t 5 /nobreak > nul

echo.
echo Checking if API server is running...
curl -s --connect-timeout 5 http://localhost:5000/health > nul 2>&1
if errorlevel 1 (
    echo ERROR: Honeypot API server failed to start!
    echo Please check the API server manually.
    pause
    exit /b 1
)

echo API server is running successfully!
echo.

echo Starting Ngrok tunnel...
echo.

REM Start ngrok in the background
start "Ngrok Tunnel" cmd /c "ngrok http 5000"

echo Waiting for Ngrok to establish tunnel (8 seconds)...
timeout /t 8 /nobreak > nul

echo.
echo Retrieving Ngrok public URL...
echo.

REM Try to get the public URL from ngrok's API
curl -s http://localhost:4040/api/tunnels | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('proto') == 'https':
            print('PUBLIC URL FOUND: ' + tunnel['public_url'])
            print('')
            print('HONEYPOT API ENDPOINT: ' + tunnel['public_url'] + '/api/honeypot/')
            print('')
            print('API KEY: test_key_123')
            print('')
            print('OTHER VALID KEYS:')
            print('  - prod_key_456')
            print('  - eval_* (any key starting with ''eval_'')')
            print('  - hackathon_* (any key starting with ''hackathon_'')')
            print('')
            print('You can now access your Honeypot API at the URL above!')
            print('The Ngrok dashboard is available at: http://localhost:4040')
            break
    else:
        print('Could not retrieve Ngrok URL automatically.')
        print('Please check the Ngrok window for the public URL.')
        print('Ngrok dashboard: http://localhost:4040')
except:
    print('Could not retrieve Ngrok URL automatically.')
    print('Please check the Ngrok window for the public URL.')
    print('Ngrok dashboard: http://localhost:4040')
"

echo.
echo ============================================
echo SERVICES RUNNING:
echo 1. API Server: http://localhost:5000
echo 2. Ngrok Tunnel: Check Ngrok window or visit http://localhost:4040
echo 3. Web Interface: Open honeypot_tester.html in browser
echo ============================================
echo.
echo Press any key to see the Ngrok dashboard...
pause > nul
start http://localhost:4040
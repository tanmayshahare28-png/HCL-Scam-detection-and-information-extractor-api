@echo off
chcp 65001 > nul
echo.
echo ============================================
echo HONEYPOT API - MULTI-AGENT SYSTEM STARTUP
echo ============================================
echo.

echo 1. Installing minimal dependencies...
pip install -r requirements_minimal.txt

echo.
echo 2. Starting API server in background...
start "API Server" cmd /c "cd api && python main_multi_agent.py"

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
echo 6. API will be available at the ngrok URL shown in the tunnel window
echo.
echo AGENTS AVAILABLE:
echo   - Financial Security Agent (Bank Fraud)
echo   - Payment Security Agent (UPI Fraud) 
echo   - Investment Advisor Agent (Investment Scams)
echo   - Skeptic Agent (Lottery Scams)
echo   - IT Security Agent (Tech Support Scams)
echo   - Policy Holder Agent (Insurance Fraud)
echo   - Tax Compliance Agent (Tax Fraud)
echo   - Credit Conscious Agent (Loan Fraud)
echo   - Cyber Security Agent (Phishing)
echo   - Relationship Skeptic Agent (Romance Scams)
echo   - Career Conscious Agent (Job Fraud)
echo   - Donation Verifier Agent (Charity Fraud)
echo   - General Assistant Agent (Normal Messages)
echo.
echo API KEYS:
echo   - test_key_123 (Primary test key)
echo   - Any key starting with 'eval_' 
echo   - Any key starting with 'hackathon_'
echo.
pause
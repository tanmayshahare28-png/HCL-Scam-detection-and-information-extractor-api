@echo off
chcp 65001 > nul
echo.
echo ============================================
echo HONEYPOT API - VALIDATION SCRIPT
echo ============================================
set /p apiUrl="Enter your public API URL (without trailing slash, e.g., http://xxxxxx.serveo.net): "

echo.
echo 1. Testing health endpoint...
curl %apiUrl%/health
echo.
echo.

echo 2. Testing without API key (should return error)...
curl -X POST %apiUrl%/api/honeypot/ ^
  -H "Content-Type: application/json" ^
  -d "{\"sessionId\":\"validation-test\",\"message\":{\"sender\":\"scammer\",\"text\":\"Test message\",\"timestamp\":1234567890}}"
echo.
echo.

echo 3. Testing with valid API key (should succeed)...
curl -X POST %apiUrl%/api/honeypot/ ^
  -H "x-api-key: test_key_123" ^
  -H "Content-Type: application/json" ^
  -d "{\"sessionId\":\"validation-test\",\"message\":{\"sender\":\"scammer\",\"text\":\"Your bank account is blocked! Verify at http://fake-bank.com\",\"timestamp\":1234567890}}"
echo.
echo.

echo 4. Testing scam detection with UPI request...
curl -X POST %apiUrl%/api/honeypot/ ^
  -H "x-api-key: test_key_123" ^
  -H "Content-Type: application/json" ^
  -d "{\"sessionId\":\"validation-test\",\"message\":{\"sender\":\"scammer\",\"text\":\"You won Rs.5000! Share your UPI ID to claim: winner@ybl\",\"timestamp\":1234567890}}"
echo.
echo.

echo 5. Testing normal message (should not detect scam)...
curl -X POST %apiUrl%/api/honeypot/ ^
  -H "x-api-key: test_key_123" ^
  -H "Content-Type: application/json" ^
  -d "{\"sessionId\":\"validation-test\",\"message\":{\"sender\":\"friend\",\"text\":\"Hey, how are you doing today?\",\"timestamp\":1234567890}}"
echo.
echo.

echo.
echo ============================================
echo VALIDATION COMPLETE
echo ============================================
echo Remember to submit your public URL with test key: test_key_123
echo.
pause
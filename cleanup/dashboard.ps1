# Honeypot API Dashboard - PowerShell Version
# Shows real-time status of all components

function Show-Dashboard {
    Clear-Host
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "    HONEYPOT API MONITORING DASHBOARD" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "TIME: $(Get-Date)" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "STATUS OF COMPONENTS:" -ForegroundColor Green
    Write-Host "====================" -ForegroundColor Green
    Write-Host ""

    # 1. API Server Status
    Write-Host "[1] API SERVER:" -ForegroundColor White
    try {
        $apiResponse = Invoke-RestMethod -Uri "http://localhost:5000/" -TimeoutSec 10
        Write-Host "    | STATUS: RUNNING - OK" -ForegroundColor Green
        Write-Host "    | VERSION: $($apiResponse.version)" -ForegroundColor White
        Write-Host "    | MODE: $($apiResponse.mode)" -ForegroundColor White
        Write-Host "    | AGENTS: $($apiResponse.agent_personalities_available)" -ForegroundColor White
    }
    catch {
        Write-Host "    | STATUS: ERROR - Possibly Down" -ForegroundColor Red
        Write-Host "    | ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # 2. Ngrok Status
    Write-Host "[2] NGROK TUNNEL:" -ForegroundColor White
    try {
        $tunnelResponse = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 10
        if ($tunnelResponse.tunnels.Count -gt 0) {
            $publicUrl = $tunnelResponse.tunnels[0].public_url
            Write-Host "    | STATUS: RUNNING - OK" -ForegroundColor Green
            Write-Host "    | PUBLIC URL: $publicUrl" -ForegroundColor White
            Write-Host "    | LOCAL ADDR: $($tunnelResponse.tunnels[0].config.addr)" -ForegroundColor White
        } else {
            Write-Host "    | STATUS: No tunnels found" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "    | STATUS: ERROR - Possibly Down" -ForegroundColor Red
        Write-Host "    | ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # 3. Monitoring Script Status
    Write-Host "[3] MONITORING SCRIPT:" -ForegroundColor White
    $monitorProcesses = Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*monitor_honeypot_with_email*" }
    if ($monitorProcesses) {
        Write-Host "    | STATUS: RUNNING - OK" -ForegroundColor Green
        Write-Host "    | PROCESS ID: $($monitorProcesses[0].Id)" -ForegroundColor White
        Write-Host "    | COMMAND: $($monitorProcesses[0].CommandLine)" -ForegroundColor White
    } else {
        Write-Host "    | STATUS: NOT RUNNING" -ForegroundColor Red
    }
    Write-Host ""

    # 4. Active Processes
    Write-Host "[4] ACTIVE PROCESSES:" -ForegroundColor White
    $apiProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*main_multi_agent*" }
    if ($apiProcesses) {
        Write-Host "    | API Server (Python): RUNNING (PID: $($apiProcesses[0].Id))" -ForegroundColor Green
    } else {
        Write-Host "    | API Server (Python): NOT FOUND" -ForegroundColor Red
    }

    $ngrokProcesses = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
    if ($ngrokProcesses) {
        Write-Host "    | Ngrok: RUNNING (PID: $($ngrokProcesses[0].Id))" -ForegroundColor Green
    } else {
        Write-Host "    | Ngrok: NOT FOUND" -ForegroundColor Red
    }
    Write-Host ""

    # 5. Recent Log Entries
    Write-Host "[5] RECENT LOG ENTRIES:" -ForegroundColor White
    $logPath = "C:\honeypot-api-project\logs\monitor.log"
    if (Test-Path $logPath) {
        $recentLogs = Get-Content $logPath | Select-Object -Last 5
        if ($recentLogs) {
            foreach ($log in $recentLogs) {
                if ($log -match "\[ERROR\]") {
                    Write-Host "    $log" -ForegroundColor Red
                } elseif ($log -match "\[ALERT\]") {
                    Write-Host "    $log" -ForegroundColor Yellow
                } else {
                    Write-Host "    $log" -ForegroundColor White
                }
            }
        } else {
            Write-Host "    No recent log entries" -ForegroundColor Gray
        }
    } else {
        Write-Host "    Log file not found. Creating directory..." -ForegroundColor Yellow
        $logDir = Split-Path $logPath -Parent
        if (!(Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force
        }
    }
    Write-Host ""

    # 6. Test API Functionality
    Write-Host "[6] API FUNCTIONALITY TEST:" -ForegroundColor White
    try {
        $testResponse = Invoke-RestMethod -Uri "https://edmond-toadless-agelessly.ngrok-free.dev/api/honeypot/" -Method Post -Headers @{
            "x-api-key" = "test_key_123"
            "Content-Type" = "application/json"
        } -Body (@{
            sessionId = "dashboard-test"
            message = @{
                sender = "scammer"
                text = "Dashboard connectivity test"
                timestamp = [int][double]::Parse((Get-Date -UFormat %s))
            }
            conversationHistory = @()
            metadata = @{
                channel = "SMS"
                language = "English"
                locale = "IN"
            }
        } | ConvertTo-Json -Depth 5) -TimeoutSec 15

        Write-Host "    | TEST: SUCCESSFUL" -ForegroundColor Green
        Write-Host "    | RESPONSE TIME: $($testResponse.sessionStats.responseTime)s" -ForegroundColor White
        Write-Host "    | AGENT: $($testResponse.agentInfo.activeAgent)" -ForegroundColor White
    }
    catch {
        Write-Host "    | TEST: FAILED" -ForegroundColor Red
        Write-Host "    | ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "REFRESHING IN 30 SECONDS... (Press Ctrl+C to exit)" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
}

# Main loop
while ($true) {
    Show-Dashboard
    Start-Sleep -Seconds 30
}
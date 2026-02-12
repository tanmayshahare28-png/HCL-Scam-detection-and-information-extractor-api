# Simple monitoring script for Honeypot API

# Configuration
$apiUrl = "http://localhost:5000/"
$ngrokUrl = "http://localhost:4040/api/tunnels"
$logPath = "C:\honeypot-api-project\logs\monitor.log"
$checkInterval = 300  # 5 minutes

# Create logs directory if it doesn't exist
$logsDir = Split-Path $logPath -Parent
if (!(Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force
}

# Track service status
$lastApiStatus = $true
$lastNgrokStatus = $true

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $logPath -Value $logEntry
    Write-Host $logEntry
}

function Send-Desktop-Notification {
    param([string]$Title, [string]$Message)
    
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        
        $template = @"
<toast>
    <visual>
        <binding template="ToastText02">
            <text id="1">$Title</text>
            <text id="2">$Message</text>
        </binding>
    </visual>
</toast>
"@
        
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Honeypot Monitor").Show($toast)
    }
    catch {
        Write-Log "Failed to send desktop notification: $_" "ERROR"
    }
}

function Send-Discord-Notification {
    param([string]$Title, [string]$Message)
    
    $webhookUrl = "https://discord.com/api/webhooks/1469004694381920347/IR_mSdyiK5kEk6lJiPyitwWm5AsTssmc_iePKnczID6ZbtmmaA6lCs1QOmrpB2kp8eNg"
    
    try {
        $payload = @{
            username = "Honeypot Monitor"
            embeds = @(
                @{
                    title = $Title
                    description = $Message
                    color = 16711680  # Red color for alerts
                    timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
                }
            )
        } | ConvertTo-Json -Depth 4
        
        Invoke-RestMethod -Uri $webhookUrl -Method Post -Body $payload -ContentType "application/json"
        Write-Log "Discord notification sent: $Title" "INFO"
        return $true
    }
    catch {
        Write-Log "Failed to send Discord notification: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-API-Status {
    try {
        $response = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 10
        return @{
            Success = $true
            Status = $response.status
            Version = $response.version
        }
    }
    catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

function Test-Ngrok-Status {
    try {
        $response = Invoke-RestMethod -Uri $ngrokUrl -TimeoutSec 10
        if ($response.tunnels.Count -gt 0) {
            return @{
                Success = $true
                PublicUrl = $response.tunnels[0].public_url
            }
        } else {
            return @{ Success = $false; Error = "No tunnels found" }
        }
    }
    catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

function Restart-API-Server {
    Write-Log "Restarting API server..."
    
    # Kill existing Python processes related to main_multi_agent.py
    $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*main_multi_agent*"
    }
    
    foreach ($proc in $processes) {
        try {
            $proc.Kill()
            Write-Log "Killed process $($proc.Id)"
        }
        catch {
            Write-Log "Failed to kill process $($proc.Id): $_" "ERROR"
        }
    }
    
    Start-Sleep -Seconds 5
    
    # Start the API server
    try {
        $apiPath = "C:\honeypot-api-project\api\main_multi_agent.py"
        Start-Process -FilePath "python" -ArgumentList $apiPath -WorkingDirectory "C:\honeypot-api-project\api" -WindowStyle Hidden
        Write-Log "API server started successfully"
        return $true
    }
    catch {
        Write-Log "Failed to start API server: $_" "ERROR"
        return $false
    }
}

function Restart-Ngrok {
    Write-Log "Restarting ngrok..."
    
    # Kill existing ngrok processes
    $ngrokProcesses = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
    foreach ($proc in $ngrokProcesses) {
        try {
            $proc.Kill()
            Write-Log "Killed ngrok process $($proc.Id)"
        }
        catch {
            Write-Log "Failed to kill ngrok process $($proc.Id): $_" "ERROR"
        }
    }
    
    Start-Sleep -Seconds 5
    
    # Start ngrok
    try {
        Start-Process -FilePath "ngrok" -ArgumentList "http 5000" -WindowStyle Hidden
        Write-Log "Ngrok started successfully"
        return $true
    }
    catch {
        Write-Log "Failed to start ngrok: $_" "ERROR"
        return $false
    }
}

Write-Log "Starting Honeypot API Monitor"
Write-Log "Check interval: $checkInterval seconds"
Write-Log "Log file: $logPath"

# Main monitoring loop
while ($true) {
    Write-Log "Checking services..."
    
    # Test API status
    $apiStatus = Test-API-Status
    if ($apiStatus.Success) {
        Write-Log "API is running - Version: $($apiStatus.Version)" "INFO"
        
        # If API was previously down, send recovery notification
        if (-not $lastApiStatus) {
            $subject = "Honeypot API - RECOVERED"
            $body = "The Honeypot API service has recovered and is now running normally.`n`n" +
                   "Time: $(Get-Date)`n" +
                   "Version: $($apiStatus.Version)`n" +
                   "Public URL: https://edmond-toadless-agelessly.ngrok-free.dev"
            
            Send-Discord-Notification -Title $subject -Message $body
        }
        
        $lastApiStatus = $true
    } else {
        $errorMessage = "API is DOWN - Error: $($apiStatus.Error)"
        Write-Log $errorMessage "ERROR"
        
        # Only send notification if this is the first time it went down
        if ($lastApiStatus) {
            $subject = "URGENT: Honeypot API - SERVICE DOWN"
            $body = "The Honeypot API service is currently DOWN.`n`n" +
                   "Time: $(Get-Date)`n" +
                   "Error: $($apiStatus.Error)`n`n" +
                   "Attempting to restart automatically..."
            
            Send-Discord-Notification -Title $subject -Message $body
            Send-Desktop-Notification "Honeypot API DOWN" "Service is down, attempting restart"
        }
        
        $restartSuccess = Restart-API-Server
        if ($restartSuccess) {
            Write-Log "API restarted successfully" "INFO"
            Send-Desktop-Notification "Honeypot API Restarted" "API server was down and has been restarted"
        } else {
            Write-Log "Failed to restart API server" "ERROR"
            Send-Desktop-Notification "Honeypot API Failed" "API server failed to restart"
        }
        
        $lastApiStatus = $false
    }
    
    # Test ngrok status
    $ngrokStatus = Test-Ngrok-Status
    if ($ngrokStatus.Success) {
        Write-Log "Ngrok is running - URL: $($ngrokStatus.PublicUrl)" "INFO"
        
        # If ngrok was previously down, send recovery notification
        if (-not $lastNgrokStatus) {
            $subject = "Ngrok Tunnel - RECOVERED"
            $body = "The Ngrok tunnel service has recovered and is now running normally.`n`n" +
                   "Time: $(Get-Date)`n" +
                   "URL: $($ngrokStatus.PublicUrl)"
            
            Send-Discord-Notification -Title $subject -Message $body
        }
        
        $lastNgrokStatus = $true
    } else {
        $errorMessage = "Ngrok is DOWN - Error: $($ngrokStatus.Error)"
        Write-Log $errorMessage "ERROR"
        
        # Only send notification if this is the first time it went down
        if ($lastNgrokStatus) {
            $subject = "URGENT: Ngrok Tunnel - SERVICE DOWN"
            $body = "The Ngrok tunnel service is currently DOWN.`n`n" +
                   "Time: $(Get-Date)`n" +
                   "Error: $($ngrokStatus.Error)`n`n" +
                   "Attempting to restart automatically...`n`n" +
                   "Public URL will change after restart."
            
            Send-Discord-Notification -Title $subject -Message $body
            Send-Desktop-Notification "Ngrok DOWN" "Tunnel is down, attempting restart"
        }
        
        $restartSuccess = Restart-Ngrok
        if ($restartSuccess) {
            Write-Log "Ngrok restarted successfully" "INFO"
            Send-Desktop-Notification "Ngrok Restarted" "Ngrok tunnel was down and has been restarted"
        } else {
            Write-Log "Failed to restart ngrok" "ERROR"
            Send-Desktop-Notification "Ngrok Failed" "Ngrok tunnel failed to restart"
        }
        
        $lastNgrokStatus = $false
    }
    
    Write-Log "Waiting $checkInterval seconds before next check..."
    Start-Sleep -Seconds $checkInterval
}
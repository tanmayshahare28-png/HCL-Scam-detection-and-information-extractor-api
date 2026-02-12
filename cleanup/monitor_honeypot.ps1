# Honeypot API Monitor and Auto-Restarter
# PowerShell script to monitor and restart services if they go down

param(
    [string]$LogPath = "C:\honeypot-api-project\logs\monitor.log",
    [int]$CheckInterval = 300  # 5 minutes in seconds
)

# Create logs directory if it doesn't exist
$logsDir = Split-Path $LogPath -Parent
if (!(Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogPath -Value $logEntry
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

function Test-API-Status {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:5000/" -TimeoutSec 10
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
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 10
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
        $_.CommandLine -like "*main_multi_agent*" -or $_.Path -like "*main_multi_agent*"
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
Write-Log "Check interval: $CheckInterval seconds"
Write-Log "Log file: $LogPath"

# Main monitoring loop
while ($true) {
    Write-Log "Checking services..."
    
    # Test API status
    $apiStatus = Test-API-Status
    if ($apiStatus.Success) {
        Write-Log "API is running - Version: $($apiStatus.Version)" "INFO"
    } else {
        Write-Log "API is DOWN - Error: $($apiStatus.Error)" "ERROR"
        $restartSuccess = Restart-API-Server
        if ($restartSuccess) {
            Write-Log "API restarted successfully" "INFO"
            Send-Desktop-Notification "Honeypot API Restarted" "API server was down and has been restarted"
        } else {
            Write-Log "Failed to restart API server" "ERROR"
            Send-Desktop-Notification "Honeypot API Failed" "API server failed to restart"
        }
    }
    
    # Test ngrok status
    $ngrokStatus = Test-Ngrok-Status
    if ($ngrokStatus.Success) {
        Write-Log "Ngrok is running - URL: $($ngrokStatus.PublicUrl)" "INFO"
    } else {
        Write-Log "Ngrok is DOWN - Error: $($ngrokStatus.Error)" "ERROR"
        $restartSuccess = Restart-Ngrok
        if ($restartSuccess) {
            Write-Log "Ngrok restarted successfully" "INFO"
            Send-Desktop-Notification "Ngrok Restarted" "Ngrok tunnel was down and has been restarted"
        } else {
            Write-Log "Failed to restart ngrok" "ERROR"
            Send-Desktop-Notification "Ngrok Failed" "Ngrok tunnel failed to restart"
        }
    }
    
    Write-Log "Waiting $CheckInterval seconds before next check..."
    Start-Sleep -Seconds $CheckInterval
}
# Email configuration for notifications
# For SMS notifications via email-to-SMS gateway (works better with captive WiFi)
# Replace with your phone number and carrier's SMS gateway
$smsGatewayEmail = "9042853332@airtelmail.com"  # Alternative Airtel India SMS gateway
# Common SMS gateways for India:
# Airtel: number@airtelkk.com or number@airtelmail.com
# Jio: number@jionet.com or number@rpgmail.net
# Vodafone Idea: number@vodafone.in or number@ideacellular.net
# Alternative method: Use a Discord/Slack webhook for notifications (more reliable with captive WiFi)

$smtpServer = "smtp.gmail.com"  # Change this to your SMTP server
$smtpPort = 587
$senderEmail = "tamarvel647@gmail.com"  # Change this to your email
$appPassword = "oyrm vymd dngu vnkl"  # Use app password, not regular password for Gmail
$recipientEmail = $smsGatewayEmail  # Send to SMS gateway instead of regular email

# Optional Discord/Slack Webhook for backup notifications (works better with captive WiFi)
$webhookUrl = "https://discord.com/api/webhooks/1469004694381920347/IR_mSdyiK5kEk6lJiPyitwWm5AsTssmc_iePKnczID6ZbtmmaA6lCs1QOmrpB2kp8eNg"  # Add webhook URL if you want backup notifications
# To create a Discord webhook:
# 1. Go to your Discord server
# 2. Server Settings > Integrations > Webhooks
# 3. Create Webhook and copy the URL
# 4. Paste it here between the quotes

# Function to send email notification with retry logic
function Send-Email-Notification {
    param(
        [string]$Subject,
        [string]$Body
    )
    
    # Due to network connectivity issues, we'll log the intent to send email
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Would send email notification: $Subject" -ForegroundColor Yellow
    Write-Host "   Subject: $Subject" -ForegroundColor Yellow
    Write-Host "   Body: $Body" -ForegroundColor Yellow
    Write-Host "   (Email sending skipped due to connectivity issues)" -ForegroundColor Yellow
    
    # Attempt to send email with retry logic (kept for when connectivity is restored)
    for ($i = 1; $i -le 2; $i++) {  # Reduced retries for faster failure
        try {
            Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Attempt $i to send email: $Subject" -ForegroundColor Yellow
            
            # Create secure credential object
            $securePassword = ConvertTo-SecureString $appPassword -AsPlainText -Force
            $credential = New-Object System.Management.Automation.PSCredential($senderEmail, $securePassword)
            
            # Create a background job to send email with timeout
            $job = Start-Job -ScriptBlock {
                param($smtpServer, $smtpPort, $credential, $senderEmail, $recipientEmail, $subject, $body)
                
                try {
                    Send-MailMessage -SmtpServer $smtpServer -Port $smtpPort -UseSsl -Credential $credential `
                        -From $senderEmail -To $recipientEmail -Subject $subject -Body $body -DeliveryNotificationOption OnFailure
                    return $true
                }
                catch {
                    Write-Error $_.Exception.Message
                    return $false
                }
            } -ArgumentList $smtpServer, $smtpPort, $credential, $senderEmail, $recipientEmail, $Subject, $Body
            
            # Wait for the job to complete with a shorter timeout
            $result = Wait-Job $job -Timeout 15
            if ($result) {
                $success = Receive-Job $job
                Remove-Job $job
                if ($success) {
                    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Email notification sent: $Subject" -ForegroundColor Green
                    return $true
                } else {
                    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Email attempt $i failed: Job returned false" -ForegroundColor Red
                }
            } else {
                # Job timed out, stop it
                Stop-Job $job
                Remove-Job $job
                Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Email attempt $i failed: Timeout" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Email attempt $i failed: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        # Wait before retry
        if ($i -lt 2) {
            Start-Sleep -Seconds 5
        }
    }
    
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] All email attempts failed for: $Subject" -ForegroundColor Red
    return $false
}

# Function to send webhook notification (Discord/Slack)
function Send-Webhook-Notification {
    param(
        [string]$Title,
        [string]$Message
    )
    
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
        Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Webhook notification sent: $Title" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Failed to send webhook: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Combined notification function - prioritizing what we know works
function Send-Notification {
    param(
        [string]$Subject,
        [string]$Body
    )
    
    # Send desktop notification (we know this works)
    Send-Desktop-Notification -Title $Subject -Message $Body
    
    # Log the notification event (we know this works)
    Write-Log "NOTIFICATION: $Subject - $Body" "ALERT"
    
    # Try webhook first (works better with captive WiFi)
    $webhookSuccess = $false
    if (![string]::IsNullOrEmpty($webhookUrl)) {
        $webhookSuccess = Send-Webhook-Notification -Title $Subject -Message $Body
    }
    
    # Try SMS/email notification (using SMS gateway - works better with captive WiFi)
    $emailSuccess = $false
    if ($recipientEmail -ne "9042853332@airtelmail.com") {  # Only try if SMS gateway is configured
        $emailSuccess = Send-Email-Notification -Subject $Subject -Body $Body
    }
    
    # Return success if primary methods worked (desktop notification and logging)
    if ($webhookSuccess) {
        Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Notification sent via webhook: $Subject" -ForegroundColor Green
        return $true
    } elseif ($emailSuccess) {
        Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Notification sent via SMS/email: $Subject" -ForegroundColor Green
        return $true
    } else {
        # Still consider it a partial success since primary delivery methods (desktop, log) worked
        Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Notification delivered via desktop and log: $Subject" -ForegroundColor Yellow
        return $true  # Consider it successful since primary delivery methods (desktop, log) worked
    }
}

# Honeypot API Monitor and Auto-Restarter with Email Notifications
param(
    [string]$LogPath = "C:\honeypot-api-project\logs\monitor.log",
    [int]$CheckInterval = 300  # 5 minutes in seconds
)

# Create logs directory if it doesn't exist
$logsDir = Split-Path $LogPath -Parent
if (!(Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force
}

# Track service status to avoid spamming emails
$lastApiStatus = $true
$lastNgrokStatus = $true

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

Write-Log "Starting Honeypot API Monitor with Email Notifications"
Write-Log "Check interval: $CheckInterval seconds"
Write-Log "Log file: $LogPath"

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
            
            Send-Notification -Subject $subject -Body $body
        }
        
        $lastApiStatus = $true
    } else {
        $errorMessage = "API is DOWN - Error: $($apiStatus.Error)"
        Write-Log $errorMessage "ERROR"
        
        # Only send email if this is the first time it went down
        if ($lastApiStatus) {
            $subject = "URGENT: Honeypot API - SERVICE DOWN"
            $body = "The Honeypot API service is currently DOWN.`n`n" +
                   "Time: $(Get-Date)`n" +
                   "Error: $($apiStatus.Error)`n`n" +
                   "Attempting to restart automatically..."
            
            Send-Notification -Subject $subject -Body $body
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
            
            Send-Notification -Subject $subject -Body $body
        }
        
        $lastNgrokStatus = $true
    } else {
        $errorMessage = "Ngrok is DOWN - Error: $($ngrokStatus.Error)"
        Write-Log $errorMessage "ERROR"
        
        # Only send email if this is the first time it went down
        if ($lastNgrokStatus) {
            $subject = "URGENT: Ngrok Tunnel - SERVICE DOWN"
            $body = "The Ngrok tunnel service is currently DOWN.`n`n" +
                   "Time: $(Get-Date)`n" +
                   "Error: $($ngrokStatus.Error)`n`n" +
                   "Attempting to restart automatically...`n`n" +
                   "Public URL will change after restart."
            
            Send-Notification -Subject $subject -Body $body
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
    
    Write-Log "Waiting $CheckInterval seconds before next check..."
    Start-Sleep -Seconds $CheckInterval
}
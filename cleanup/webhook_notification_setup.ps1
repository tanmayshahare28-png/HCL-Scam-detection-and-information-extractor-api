# Alternative notification system using webhooks (Discord/Slack)
# This is more likely to work in restricted network environments

# Webhook URL - you can create one of these:
# For Discord: Server Settings > Integrations > Webhooks > New Webhook
# For Slack: Create an app and configure incoming webhooks
$webhookUrl = ""  # You'll need to provide your webhook URL

# Function to send webhook notification
function Send-Webhook-Notification {
    param(
        [string]$Title,
        [string]$Message
    )
    
    if ([string]::IsNullOrEmpty($webhookUrl)) {
        Write-Host "No webhook URL configured. Please set up a webhook URL." -ForegroundColor Red
        return $false
    }
    
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
        
        $response = Invoke-RestMethod -Uri $webhookUrl -Method Post -Body $payload -ContentType "application/json"
        Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Webhook notification sent: $Title" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Failed to send webhook: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test webhook notification
Write-Host "Testing webhook notification system..." -ForegroundColor Yellow

if ([string]::IsNullOrEmpty($webhookUrl)) {
    Write-Host "No webhook URL configured." -ForegroundColor Red
    Write-Host "To set up webhook notifications:" -ForegroundColor Yellow
    Write-Host "1. For Discord: Go to Server Settings > Integrations > Webhooks > New Webhook" -ForegroundColor Yellow
    Write-Host "2. Copy the webhook URL and paste it in the script" -ForegroundColor Yellow
    Write-Host "3. For Slack: Create an app and configure incoming webhooks" -ForegroundColor Yellow
    Write-Host "" -ForegroundColor Yellow
    Write-Host "Alternatively, you can use email-to-SMS gateways:" -ForegroundColor Yellow
    Write-Host "For example, to send to a Verizon number: number@vtext.com" -ForegroundColor Yellow
    Write-Host "Or use other carrier gateways for SMS notifications" -ForegroundColor Yellow
} else {
    $testSuccess = Send-Webhook-Notification -Title "Test Notification" -Message "This is a test notification from your Honeypot API monitor."
    
    if ($testSuccess) {
        Write-Host "Webhook test successful!" -ForegroundColor Green
    } else {
        Write-Host "Webhook test failed." -ForegroundColor Red
    }
}

# For SMS notifications via email gateway (alternative method)
Write-Host "`nAlternative: SMS notifications via email gateway" -ForegroundColor Cyan
Write-Host "You can send notifications to your phone via email-to-SMS gateways:" -ForegroundColor White
Write-Host "Verizon: number@vtext.com" -ForegroundColor White
Write-Host "AT&T: number@txt.att.net" -ForegroundColor White
Write-Host "T-Mobile: number@tmomail.net" -ForegroundColor White
Write-Host "Sprint: number@messaging.sprintpcs.com" -ForegroundColor White
Write-Host "For international carriers, search for 'carrier SMS gateway'" -ForegroundColor White
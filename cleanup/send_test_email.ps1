# Test email script for honeypot monitor
# Reads credentials from the config file and sends a test email

# Read the email configuration
$configPath = "C:\honeypot-api-project\email_config.txt"
$config = @{}

if (Test-Path $configPath) {
    Get-Content $configPath | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            $config[$key] = $value
        }
    }
} else {
    Write-Host "Configuration file not found: $configPath" -ForegroundColor Red
    exit 1
}

# Extract configuration values
$smtpServer = $config["SMTPServer"]
$smtpPort = [int]$config["SMTPPort"]
$username = $config["Username"]
$appPassword = $config["AppPassword"]
$recipient = $config["RecipientEmail"]

Write-Host "Using configuration:" -ForegroundColor Yellow
Write-Host "  SMTP Server: $smtpServer" -ForegroundColor Yellow
Write-Host "  SMTP Port: $smtpPort" -ForegroundColor Yellow
Write-Host "  Username: $username" -ForegroundColor Yellow
Write-Host "  Recipient: $recipient" -ForegroundColor Yellow

# Create secure credential
$securePassword = ConvertTo-SecureString $appPassword -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($username, $securePassword)

# Create email parameters
$subject = "Honeypot API Monitor - Test Email"
$body = @"
Hello,

This is a test email from your Honeypot API monitoring system.

Your email notification system is properly configured and working!

Time: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Status: TEST EMAIL SENT SUCCESSFULLY

Your 6-day monitoring system is ready to notify you if your API goes offline.

Best regards,
Honeypot API Monitor
"@

try {
    Write-Host "Attempting to send test email..." -ForegroundColor Cyan
    
    # Send the email with timeout protection
    $job = Start-Job -ScriptBlock {
        param($smtpServer, $smtpPort, $credential, $username, $recipient, $subject, $body)
        
        try {
            Send-MailMessage -SmtpServer $smtpServer -Port $smtpPort -UseSsl -Credential $credential `
                -From $username -To $recipient -Subject $subject -Body $body -DeliveryNotificationOption OnFailure
            return $true
        }
        catch {
            Write-Error $_.Exception.Message
            return $false
        }
    } -ArgumentList $smtpServer, $smtpPort, $credential, $username, $recipient, $subject, $body
    
    # Wait for the job to complete with a timeout of 60 seconds
    $result = Wait-Job $job -Timeout 60
    if ($result) {
        $success = Receive-Job $job
        Remove-Job $job
        if ($success) {
            Write-Host "SUCCESS: Test email sent to $recipient" -ForegroundColor Green
            Write-Host "Please check your inbox (and spam folder) for the test email." -ForegroundColor Green
        } else {
            Write-Host "FAILURE: Could not send test email - job returned false" -ForegroundColor Red
        }
    } else {
        # Job timed out, stop it
        Stop-Job $job
        Remove-Job $job
        Write-Host "FAILURE: Could not send test email - timeout after 60 seconds" -ForegroundColor Red
    }
}
catch {
    Write-Host "FAILURE: Error sending test email - $($_.Exception.Message)" -ForegroundColor Red
}
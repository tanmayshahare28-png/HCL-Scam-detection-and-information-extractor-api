# Test SMS notification to Airtel India
# Reads the configuration from the main monitoring script

# Load the configuration by reading the file
$configContent = Get-Content "C:\honeypot-api-project\monitor_honeypot_with_email.ps1" -Raw

# Extract the configuration values using regex
$smtpServer = [regex]::Match($configContent, '\$smtpServer = "(.*?)"').Groups[1].Value
$smtpPort = [regex]::Match($configContent, '\$smtpPort = (\d+)').Groups[1].Value
$senderEmail = [regex]::Match($configContent, '\$senderEmail = "(.*?)"').Groups[1].Value
$appPassword = [regex]::Match($configContent, '\$appPassword = "(.*?)"').Groups[1].Value

# Extract recipient email (which is set to $smsGatewayEmail, so we need to find the $smsGatewayEmail value)
$smsGatewayEmail = [regex]::Match($configContent, '\$smsGatewayEmail = "(.*?)"').Groups[1].Value
$recipientEmail = $smsGatewayEmail

Write-Host "Testing SMS notification to Airtel India..." -ForegroundColor Cyan
Write-Host "Using configuration:" -ForegroundColor Yellow
Write-Host "  SMTP Server: $smtpServer" -ForegroundColor Yellow
Write-Host "  SMTP Port: $smtpPort" -ForegroundColor Yellow
Write-Host "  Sender: $senderEmail" -ForegroundColor Yellow
Write-Host "  Recipient (SMS): $recipientEmail" -ForegroundColor Yellow

# Create secure credential
$securePassword = ConvertTo-SecureString $appPassword -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($senderEmail, $securePassword)

# Create email parameters for SMS
$subject = "Honeypot Monitor - Test SMS"
$body = @"
TEST SMS from Honeypot API Monitor

Your SMS notification system is configured correctly!

Time: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Status: TEST SMS SENT SUCCESSFULLY

This confirms your Airtel India SMS gateway is working.
Your 6-day monitoring system will notify you if your API goes offline.

Best regards,
Honeypot API Monitor
"@

try {
    Write-Host "`nAttempting to send test SMS..." -ForegroundColor Cyan
    
    # Send the email/SMS with timeout protection
    $job = Start-Job -ScriptBlock {
        param($smtpServer, $smtpPort, $credential, $senderEmail, $recipientEmail, $subject, $body)
        
        try {
            $smtp = New-Object System.Net.Mail.SmtpClient($smtpServer, $smtpPort)
            $smtp.EnableSsl = $true
            $smtp.Credentials = New-Object System.Net.NetworkCredential($senderEmail.Split('@')[0], ($using:credential).GetNetworkCredential().Password)
            
            $msg = New-Object System.Net.Mail.MailMessage($senderEmail, $recipientEmail, $subject, $body)
            $smtp.Send($msg)
            return $true
        }
        catch {
            return $_.Exception.Message
        }
    } -ArgumentList $smtpServer, $smtpPort, $credential, $senderEmail, $recipientEmail, $subject, $body
    
    # Wait for the job to complete with a timeout of 30 seconds
    $result = Wait-Job $job -Timeout 30
    if ($result) {
        $jobResult = Receive-Job $job
        Remove-Job $job
        if ($jobResult -eq $true) {
            Write-Host "`nSUCCESS: Test SMS sent to $recipientEmail" -ForegroundColor Green
            Write-Host "Please check your phone for the test SMS." -ForegroundColor Green
        } else {
            Write-Host "`nSMS SEND FAILED: $jobResult" -ForegroundColor Red
            Write-Host "This could be due to:" -ForegroundColor Red
            Write-Host "  - Incorrect SMS gateway for Airtel India" -ForegroundColor Red
            Write-Host "  - Network/captive WiFi restrictions" -ForegroundColor Red
            Write-Host "  - Carrier blocking email-to-SMS gateways" -ForegroundColor Red
            Write-Host "  - Gmail security settings" -ForegroundColor Red
        }
    } else {
        # Job timed out, stop it
        Stop-Job $job
        Remove-Job $job
        Write-Host "`nSMS SEND TIMEOUT: The attempt timed out after 30 seconds" -ForegroundColor Red
    }
}
catch {
    Write-Host "`nSMS SEND ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTest completed." -ForegroundColor Cyan
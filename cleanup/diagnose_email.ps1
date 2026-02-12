# Diagnostic test for email connectivity
# Tests various aspects of email configuration

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

Write-Host "Testing email configuration..." -ForegroundColor Yellow
Write-Host "SMTP Server: $smtpServer" -ForegroundColor Yellow
Write-Host "SMTP Port: $smtpPort" -ForegroundColor Yellow
Write-Host "Username: $username" -ForegroundColor Yellow
Write-Host "Recipient: $recipient" -ForegroundColor Yellow

# Test network connectivity to SMTP server
Write-Host "`nTesting network connectivity to $smtpServer on port $smtpPort..." -ForegroundColor Cyan
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $connect = $tcpClient.BeginConnect($smtpServer, $smtpPort, $null, $null)
    $wait = $connect.AsyncWaitHandle.WaitOne(10000, $false)  # 10 second timeout
    
    if (-not $wait) {
        $tcpClient.Close()
        Write-Host "CONNECTION FAILED: Could not connect to $smtpServer on port $smtpPort" -ForegroundColor Red
        Write-Host "This could be due to:" -ForegroundColor Red
        Write-Host "  - Firewall blocking the connection" -ForegroundColor Red
        Write-Host "  - Corporate network restrictions" -ForegroundColor Red
        Write-Host "  - Incorrect SMTP server/port" -ForegroundColor Red
        exit 1
    } else {
        $tcpClient.EndConnect($connect)
        $tcpClient.Close()
        Write-Host "CONNECTION SUCCESS: Connected to $smtpServer on port $smtpPort" -ForegroundColor Green
    }
}
catch {
    Write-Host "CONNECTION FAILED: $_" -ForegroundColor Red
    exit 1
}

# Test credentials by creating a test email job
Write-Host "`nTesting email credentials..." -ForegroundColor Cyan

# Create secure credential
$securePassword = ConvertTo-SecureString $appPassword -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($username, $securePassword)

# Create email parameters
$subject = "Honeypot API Monitor - Connectivity Test"
$body = @"
This is a connectivity test from your Honeypot API monitoring system.

Network connection to SMTP server successful!

Time: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Status: NETWORK CONNECTIVITY VERIFIED

Note: Even though network connectivity is working, the actual email delivery might still fail
due to authentication issues or other SMTP-specific problems.

Best regards,
Honeypot API Monitor
"@

try {
    Write-Host "Attempting to send test email via background job..." -ForegroundColor Cyan
    
    # Send the email with timeout protection using .NET SmtpClient directly
    $smtp = New-Object System.Net.Mail.SmtpClient($smtpServer, $smtpPort)
    $smtp.EnableSsl = $true
    $smtp.Credentials = $credential
    
    $msg = New-Object System.Net.Mail.MailMessage
    $msg.From = $username
    $msg.To.Add($recipient)
    $msg.Subject = $subject
    $msg.Body = $body
    
    # Create a background job to send email with timeout
    $job = Start-Job -ScriptBlock {
        param($smtpServer, $smtpPort, $username, $password, $to, $subject, $body)
        
        try {
            $smtp = New-Object System.Net.Mail.SmtpClient($smtpServer, $smtpPort)
            $smtp.EnableSsl = $true
            $smtp.Credentials = New-Object System.Net.NetworkCredential($username, $password)
            
            $msg = New-Object System.Net.Mail.MailMessage($username, $to, $subject, $body)
            $smtp.Send($msg)
            return $true
        }
        catch {
            return $_.Exception.Message
        }
    } -ArgumentList $smtpServer, $smtpPort, $username, $appPassword, $recipient, $subject, $body
    
    # Wait for the job to complete with a timeout of 60 seconds
    $result = Wait-Job $job -Timeout 60
    if ($result) {
        $jobResult = Receive-Job $job
        Remove-Job $job
        if ($jobResult -eq $true) {
            Write-Host "SUCCESS: Test email sent successfully to $recipient" -ForegroundColor Green
            Write-Host "Please check your inbox (and spam folder) for the test email." -ForegroundColor Green
        } else {
            Write-Host "EMAIL SEND FAILED: $jobResult" -ForegroundColor Red
            Write-Host "This could be due to:" -ForegroundColor Red
            Write-Host "  - Incorrect username/password/App Password" -ForegroundColor Red
            Write-Host "  - 2FA not enabled on Gmail account" -ForegroundColor Red
            Write-Host "  - App Password not generated correctly" -ForegroundColor Red
            Write-Host "  - Gmail security settings blocking access" -ForegroundColor Red
        }
    } else {
        # Job timed out, stop it
        Stop-Job $job
        Remove-Job $job
        Write-Host "EMAIL SEND TIMEOUT: The email attempt timed out after 60 seconds" -ForegroundColor Red
    }
}
catch {
    Write-Host "EMAIL SEND ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTest completed." -ForegroundColor Cyan
# Test email configuration
param(
    [string]$ConfigPath = "C:\honeypot-api-project\email_config.txt"
)

function Send-Test-Email {
    param(
        [string]$SmtpServer,
        [int]$SmtpPort,
        [string]$Username,
        [string]$AppPassword,
        [string]$RecipientEmail
    )
    
    try {
        $securePassword = ConvertTo-SecureString $AppPassword -AsPlainText -Force
        $credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)
        
        $subject = "Honeypot API Monitor - Test Notification"
        $body = "This is a test email to confirm your email notification system is working.`n`n" +
               "Time: $(Get-Date)`n" +
               "Honeypot API Monitor is ready to send alerts when services go down."
        
        Send-MailMessage -SmtpServer $SmtpServer -Port $SmtpPort -UseSsl -Credential $credential `
            -From $Username -To $RecipientEmail -Subject $subject -Body $body -DeliveryNotificationOption OnFailure
        
        Write-Host "Test email sent successfully to $RecipientEmail" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Failed to send test email: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Read configuration from file
if (Test-Path $ConfigPath) {
    Write-Host "Reading configuration from $ConfigPath" -ForegroundColor Yellow
    
    $configContent = Get-Content $ConfigPath
    $config = @{}
    
    foreach ($line in $configContent) {
        if ($line -match "^([^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            $config[$key] = $value
        }
    }
    
    Write-Host "Configuration loaded:" -ForegroundColor Cyan
    Write-Host "  SMTP Server: $($config['SMTPServer'])"
    Write-Host "  SMTP Port: $($config['SMTPPort'])"
    Write-Host "  Username: $($config['Username'])"
    Write-Host "  Recipient: $($config['RecipientEmail'])"
    
    Write-Host "`nSending test email..." -ForegroundColor Yellow
    $success = Send-Test-Email -SmtpServer $config['SMTPServer'] -SmtpPort ([int]$config['SMTPPort']) `
        -Username $config['Username'] -AppPassword $config['AppPassword'] -RecipientEmail $config['RecipientEmail']
    
    if ($success) {
        Write-Host "`nTest email sent successfully!" -ForegroundColor Green
        Write-Host "You can now update the monitor_honeypot_with_email.ps1 script with these settings." -ForegroundColor Cyan
    } else {
        Write-Host "`nTest email failed. Please check your configuration." -ForegroundColor Red
    }
} else {
    Write-Host "Configuration file not found: $ConfigPath" -ForegroundColor Red
    Write-Host "Please create the configuration file first." -ForegroundColor Yellow
}
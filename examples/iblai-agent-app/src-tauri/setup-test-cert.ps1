# setup-test-cert.ps1
# Creates a self-signed certificate for local MSIX testing/sideloading.
# Run this ONCE before your first test build.
#
# The cert Subject (CN=iblai-agent-app-dev) must match the Publisher in AppxManifest.xml.
#
# Prerequisites: Enable Developer Mode
#   Settings > Update & Security > For developers > Developer Mode: ON
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File src-tauri\setup-test-cert.ps1

$ErrorActionPreference = "Stop"

$Subject = "CN=iblai-agent-app-dev"

# Check if cert already exists
$existing = Get-ChildItem -Path "Cert:\CurrentUser\My" | Where-Object { $_.Subject -eq $Subject }
if ($existing) {
    Write-Host "Test certificate already exists:" -ForegroundColor Green
    Write-Host "  Subject:    $($existing.Subject)" -ForegroundColor Gray
    Write-Host "  Thumbprint: $($existing.Thumbprint)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Use this thumbprint with build-msix.ps1:" -ForegroundColor Yellow
    Write-Host "  .\build-msix.ps1 -CertThumbprint `"$($existing.Thumbprint)`"" -ForegroundColor White
    exit 0
}

# Create self-signed certificate
Write-Host "Creating self-signed certificate ($Subject)..." -ForegroundColor Yellow

$cert = New-SelfSignedCertificate `
    -Type Custom `
    -Subject $Subject `
    -KeyUsage DigitalSignature `
    -FriendlyName "iblai-agent-app MSIX Test" `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3") `
    -NotAfter (Get-Date).AddYears(2)

Write-Host "Certificate created." -ForegroundColor Green
Write-Host "  Subject:    $($cert.Subject)" -ForegroundColor Gray
Write-Host "  Thumbprint: $($cert.Thumbprint)" -ForegroundColor Cyan
Write-Host "  Expires:    $($cert.NotAfter)" -ForegroundColor Gray

# Install to Trusted Root Certification Authorities (required for MSIX signature validation)
Write-Host "`nInstalling certificate to Trusted Root store..." -ForegroundColor Yellow

$store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
$store.Open("ReadWrite")
$store.Add($cert)
$store.Close()

Write-Host "Certificate installed to Trusted Root store." -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "--- Setup Complete ---" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Enable Developer Mode: Settings > Update & Security > For developers" -ForegroundColor White
Write-Host "  2. Build and sign the MSIX:" -ForegroundColor White
Write-Host "     .\build-msix.ps1 -CertThumbprint `"$($cert.Thumbprint)`"" -ForegroundColor White
Write-Host "  3. Double-click the .msix file in msix-output/ to install" -ForegroundColor White
Write-Host ""
Write-Host "To remove this certificate later:" -ForegroundColor DarkYellow
Write-Host "  Get-ChildItem Cert:\CurrentUser\My | Where-Object { `$_.Subject -eq '$Subject' } | Remove-Item" -ForegroundColor Gray
Write-Host "  Get-ChildItem Cert:\CurrentUser\Root | Where-Object { `$_.Subject -eq '$Subject' } | Remove-Item" -ForegroundColor Gray
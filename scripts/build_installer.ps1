param(
    [string]$Python = "python",
    [string]$IsccPath = "",
    [switch]$SkipExeBuild,
    [string]$Version = "",
    [string]$SignToolPath = "",
    [string]$CertFile = "",
    [string]$CertPassword = "",
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

function Test-CodeSigningCertificate {
    param(
        [string]$Path,
        [string]$Password
    )

    if (-not (Test-Path $Path)) {
        Write-Error "Certificate file not found: $Path"
        return $false
    }

    try {
        $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
        if ([string]::IsNullOrWhiteSpace($Password)) {
            $cert.Import($Path)
        } else {
            $cert.Import($Path, $Password, [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable)
        }

        if ($cert.NotAfter -lt (Get-Date)) {
            Write-Error "Certificate expired on $($cert.NotAfter.ToString('u'))."
            return $false
        }
        if ($cert.NotBefore -gt (Get-Date)) {
            Write-Error "Certificate is not valid yet until $($cert.NotBefore.ToString('u'))."
            return $false
        }
        $daysLeft = [int]($cert.NotAfter - (Get-Date)).TotalDays
        if ($daysLeft -le 30) {
            Write-Warning "Certificate expires soon: $daysLeft day(s) left."
        } else {
            Write-Host "Certificate is valid. Days left: $daysLeft"
        }
        return $true
    } catch {
        Write-Error "Failed to validate certificate: $($_.Exception.Message)"
        return $false
    }
}

if (-not $SkipExeBuild) {
    powershell -ExecutionPolicy Bypass -File "scripts/build_exe.ps1" -Python $Python
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$exePath = "dist/asutp-mixing-module.exe"
if (-not (Test-Path $exePath)) {
    Write-Error "EXE not found at $exePath. Run scripts/build_exe.ps1 first."
    exit 1
}

if ([string]::IsNullOrWhiteSpace($IsccPath)) {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $IsccPath = $candidate
            break
        }
    }
}

if ([string]::IsNullOrWhiteSpace($IsccPath) -or -not (Test-Path $IsccPath)) {
    Write-Error "Inno Setup compiler (ISCC.exe) not found. Install Inno Setup 6 or pass -IsccPath."
    exit 1
}

if ([string]::IsNullOrWhiteSpace($Version)) {
    $pyproject = Get-Content "pyproject.toml" -Raw
    if ($pyproject -match '(?m)^version\s*=\s*"([^"]+)"\s*$') {
        $Version = $matches[1]
    }
}
if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = "0.1.0"
}

& $IsccPath "/DAppVersion=$Version" "scripts/installer.iss"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$installerPath = "dist/asutp-mixing-module-setup.exe"
if (-not (Test-Path $installerPath)) {
    Write-Error "Installer output not found at $installerPath"
    exit 1
}

$shouldSign = -not [string]::IsNullOrWhiteSpace($CertFile)
if ($shouldSign) {
    if ([string]::IsNullOrWhiteSpace($SignToolPath)) {
        $sigCandidates = @(
            "${env:ProgramFiles(x86)}\Windows Kits\10\App Certification Kit\signtool.exe",
            "${env:ProgramFiles(x86)}\Windows Kits\10\bin\x64\signtool.exe",
            "${env:ProgramFiles}\Windows Kits\10\bin\x64\signtool.exe"
        )
        foreach ($candidate in $sigCandidates) {
            if (Test-Path $candidate) {
                $SignToolPath = $candidate
                break
            }
        }
    }
    if ([string]::IsNullOrWhiteSpace($SignToolPath) -or -not (Test-Path $SignToolPath)) {
        Write-Error "signtool.exe not found. Pass -SignToolPath or install Windows SDK."
        exit 1
    }
    if (-not (Test-CodeSigningCertificate -Path $CertFile -Password $CertPassword)) {
        exit 1
    }
    $filesToSign = @($exePath, $installerPath)
    foreach ($f in $filesToSign) {
        if ([string]::IsNullOrWhiteSpace($CertPassword)) {
            & $SignToolPath sign /f $CertFile /fd SHA256 /tr $TimestampUrl /td SHA256 $f
        } else {
            & $SignToolPath sign /f $CertFile /p $CertPassword /fd SHA256 /tr $TimestampUrl /td SHA256 $f
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Code signing failed for $f"
            exit $LASTEXITCODE
        }
    }
    Write-Host "Signing completed for EXE and installer."
}

Write-Host "Installer ready: $installerPath (version $Version)"

param(
    [string]$Python = "python",
    [switch]$InstallDeps
)

$ErrorActionPreference = "Stop"

Set-Location -Path (Resolve-Path "$PSScriptRoot\..")

Write-Host "Project root: $((Get-Location).Path)"

if ($InstallDeps) {
    Write-Host "Installing UI dependencies..."
    & $Python -m pip install -e ".[ui]"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$uiPath = "src/mixing_module/ui.py"
if (-not (Test-Path $uiPath)) {
    Write-Error "UI script not found: $uiPath"
    exit 1
}

Write-Host "Starting Streamlit UI..."
& $Python -m streamlit run $uiPath
exit $LASTEXITCODE

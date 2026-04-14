param(
    [string]$Python = "python",
    [switch]$Clean
)

if ($Clean) {
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
}

& $Python -m pip install -e ".[ui,packaging]"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --name "asutp-mixing-module" `
    --onefile `
    --collect-all streamlit `
    --collect-all pandas `
    --collect-all matplotlib `
    --collect-all yaml `
    "src/mixing_module/app_launcher.py"

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "EXE ready: dist/asutp-mixing-module.exe"

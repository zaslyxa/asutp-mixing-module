@echo off
setlocal

cd /d "%~dp0"

if not exist ".\scripts\start-ui-local.ps1" (
  echo [ERROR] Script not found: .\scripts\start-ui-local.ps1
  echo Please create the PowerShell script first.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\start-ui-local.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo [ERROR] start-ui-local.ps1 exited with code %EXIT_CODE%.
  pause
)

exit /b %EXIT_CODE%

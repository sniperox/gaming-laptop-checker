@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Gaming Laptop Checker Launcher
color 0A

echo [GLC] Gaming Laptop Checker - EXE launcher

set "APP_DIR=%LOCALAPPDATA%\GamingLaptopChecker"
set "EXE_PATH=%APP_DIR%\GamingLaptopChecker.exe"
set "EXE_URL=https://github.com/sniperox/gaming-laptop-checker/releases/latest/download/GamingLaptopChecker.exe"

if not exist "%APP_DIR%" mkdir "%APP_DIR%"

echo [GLC] Downloading latest GamingLaptopChecker.exe...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "Invoke-WebRequest -Uri '%EXE_URL%' -OutFile '%EXE_PATH%'"

if %errorlevel% neq 0 (
  echo [GLC] Download failed. Check EXE_URL in bootstrap.bat.
  pause
  exit /b 1
)

if not exist "%EXE_PATH%" (
  echo [GLC] EXE was not downloaded.
  pause
  exit /b 1
)

echo [GLC] Starting Gaming Laptop Checker...
start "Gaming Laptop Checker" /D "%APP_DIR%" cmd.exe /K "color 0A && GamingLaptopChecker.exe"

endlocal

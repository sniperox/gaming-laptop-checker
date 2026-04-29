param(
  [switch]$Clean
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if ($Clean) {
  Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller --quiet

.\.venv\Scripts\pyinstaller.exe .\GamingLaptopChecker.spec --noconfirm --clean

Write-Host ""
Write-Host "Built: $root\dist\GamingLaptopChecker.exe" -ForegroundColor Green
Write-Host "Upload that EXE as a GitHub Release asset named GamingLaptopChecker.exe."


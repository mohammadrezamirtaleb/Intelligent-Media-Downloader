$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Intelligent Media Downloader Setup    " -ForegroundColor Magenta
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$VenvDir = Join-Path -Path $ScriptDir -ChildPath "venv"

# Create Virtual Environment if it doesn't exist
if (-not (Test-Path -Path $VenvDir)) {
    Write-Host "Creating Python Virtual Environment..." -ForegroundColor Yellow
    python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment. Make sure python is installed." -ForegroundColor Red
        Exit
    }
}

# Activate Virtual Environment
$ActivateScript = Join-Path -Path $VenvDir -ChildPath "Scripts\Activate.ps1"
if (Test-Path -Path $ActivateScript) {
    & $ActivateScript
} else {
    Write-Host "Could not find activation script!" -ForegroundColor Red
    Exit
}

# Install Requirements
Write-Host "Checking dependencies (yt-dlp, rich)..." -ForegroundColor Yellow
python -m pip install -r (Join-Path -Path $ScriptDir -ChildPath "requirements.txt") -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "Dependency installation failed. Check your Python version and network connection." -ForegroundColor Red
    Exit $LASTEXITCODE
}

Write-Host "Dependencies installed successfully!" -ForegroundColor Green
Write-Host "Launching Downloader..." -ForegroundColor Cyan
Start-Sleep -Seconds 1

# Add deno to PATH (required for YouTube JS challenge solving)
$DenoDir = Join-Path -Path $env:USERPROFILE -ChildPath ".deno\bin"
if (Test-Path -Path $DenoDir) {
    $env:Path = "$DenoDir;$env:Path"
    Write-Host "Deno JS Runtime detected!" -ForegroundColor Green
} else {
    Write-Host "WARNING: Deno not found. YouTube may block downloads." -ForegroundColor Yellow
    Write-Host "Install deno: irm https://deno.land/install.ps1 | iex" -ForegroundColor Yellow
}

# Set UTF-8 encoding for Rich console
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# Run the script
python (Join-Path -Path $ScriptDir -ChildPath "src\youtube_downloader.py")

# Pause before closing if running from explorer
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

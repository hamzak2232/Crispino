# PowerShell script to build both windowed and console versions of Crispino POS
# Usage: .\build.ps1 [-Console] [-Windowed] [-Clean]

param(
    [switch]$Console,
    [switch]$Windowed,
    [switch]$Clean,
    [switch]$All
)

# If no specific build type is specified, build both
if (-not $Console -and -not $Windowed -and -not $All) {
    $All = $true
}

# Set error handling
$ErrorActionPreference = "Stop"

Write-Host "=== Crispino POS Build Script ===" -ForegroundColor Green

# Clean up previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path "dist") {
        Remove-Item "dist" -Recurse -Force
        Write-Host "Removed dist directory" -ForegroundColor Gray
    }
    if (Test-Path "build") {
        Remove-Item "build" -Recurse -Force
        Write-Host "Removed build directory" -ForegroundColor Gray
    }
}

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
if ($IsWindows -or $env:OS -eq "Windows_NT") {
    & ".\.venv\Scripts\Activate.ps1"
} else {
    Write-Error "This script is designed for Windows. Use bash scripts for other platforms."
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Verify PyInstaller is available
try {
    pyinstaller --version | Out-Null
    Write-Host "PyInstaller is ready" -ForegroundColor Green
} catch {
    Write-Error "PyInstaller is not available. Please ensure it's installed."
    exit 1
}

# Build console version
if ($Console -or $All) {
    Write-Host ""
    Write-Host "Building console version..." -ForegroundColor Cyan
    pyinstaller "Crispino POS (console).spec" --clean --noconfirm
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Console version built successfully" -ForegroundColor Green
        if (Test-Path "dist\Crispino POS (console).exe") {
            $size = (Get-Item "dist\Crispino POS (console).exe").Length / 1MB
            Write-Host "  Size: $([math]::Round($size, 2)) MB" -ForegroundColor Gray
        }
    } else {
        Write-Error "Console build failed with exit code $LASTEXITCODE"
        exit 1
    }
}

# Build windowed version
if ($Windowed -or $All) {
    Write-Host ""
    Write-Host "Building windowed version..." -ForegroundColor Cyan
    pyinstaller "Crispino POS.spec" --clean --noconfirm
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Windowed version built successfully" -ForegroundColor Green
        if (Test-Path "dist\Crispino POS.exe") {
            $size = (Get-Item "dist\Crispino POS.exe").Length / 1MB
            Write-Host "  Size: $([math]::Round($size, 2)) MB" -ForegroundColor Gray
        }
    } else {
        Write-Error "Windowed build failed with exit code $LASTEXITCODE"
        exit 1
    }
}

Write-Host ""
Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host "Built files are in the 'dist' directory:" -ForegroundColor Yellow

if (Test-Path "dist") {
    Get-ChildItem "dist" -Filter "*.exe" | ForEach-Object {
        $size = $_.Length / 1MB
        Write-Host "  $($_.Name) - $([math]::Round($size, 2)) MB" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "To test the builds:" -ForegroundColor Yellow
if ($Console -or $All) {
    Write-Host "  Console version: .\dist\`"Crispino POS (console).exe`"" -ForegroundColor Gray
}
if ($Windowed -or $All) {
    Write-Host "  Windowed version: .\dist\`"Crispino POS.exe`"" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Note: The first run will create a 'data' directory next to the executable" -ForegroundColor Cyan
Write-Host "and populate it with the SQLite database." -ForegroundColor Cyan
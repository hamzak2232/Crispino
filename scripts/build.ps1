[CmdletBinding()]
param(
  [ValidateSet('console','windowed')]
  [string]$Mode = 'console',
  [switch]$Clean
)

$ErrorActionPreference = 'Stop'

# Ensure PyInstaller and helpful hooks
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
  python -m pip install -U pyinstaller | Out-Null
}
python -m pip install -U pyinstaller-hooks-contrib fastapi pydantic pydantic-core | Out-Null

if ($Clean) {
  Remove-Item -Recurse -Force .\build, .\dist -ErrorAction SilentlyContinue
}

$IsConsole = $Mode -eq 'console'
$Name = if ($IsConsole) { 'CrispinoPOSConsole' } else { 'Crispino POS' }
$ModeArgs = if ($IsConsole) { @('--console') } else { @('--windowed') }

$IconArgs = @()
if (Test-Path 'assets\icon.ico') { $IconArgs = @('--icon','assets\icon.ico') }

# Find pydantic_core binary
$pydPath = Get-ChildItem ".\venv\Lib\site-packages\pydantic_core\*_pydantic_core*.pyd" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
$BinaryArgs = @()
if ($pydPath) { $BinaryArgs = @('--add-binary', "$pydPath;pydantic_core") }

# Data folders
$DataArgs = @()
if (Test-Path 'app\templates') { $DataArgs += @('--add-data','app\templates;app\templates') }
if (Test-Path 'app\static')    { $DataArgs += @('--add-data','app\static;app\static') }

$CollectArgs = @(
  '--hidden-import','sqlite3',
  '--collect-all','fastapi',
  '--collect-all','starlette',
  '--collect-all','uvicorn',
  '--collect-all','anyio',
  '--collect-all','h11',
  '--collect-all','jinja2',
  '--collect-all','pydantic',
  '--collect-all','app',
  '--hidden-import','app',
  '--hidden-import','app.main',
  '--copy-metadata','pydantic',
  '--copy-metadata','pydantic-core',
  '--hidden-import','pydantic_core._pydantic_core'
)

$Entry = 'scripts\launch.pyw'
if (-not (Test-Path $Entry)) { throw "Entry script not found at $Entry" }

$Args = @('--noconfirm','--clean','--name',$Name) + $ModeArgs + $IconArgs + $CollectArgs + $BinaryArgs + $DataArgs + @($Entry)

Write-Host "Running: pyinstaller $($Args -join ' ')" -ForegroundColor Cyan
& pyinstaller @Args
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

Write-Host "Build complete."
Write-Host "Run: .\dist\$Name\$Name.exe"
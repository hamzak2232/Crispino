@echo off
REM Simple batch script to build Crispino POS
REM This calls the PowerShell script with appropriate parameters

echo === Crispino POS Quick Build ===
echo.

REM Check if PowerShell is available
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PowerShell is not available on this system.
    echo Please run PyInstaller manually or use PowerShell.
    pause
    exit /b 1
)

REM Run the PowerShell build script
echo Running PowerShell build script...
powershell -ExecutionPolicy Bypass -File "scripts\build.ps1" -All -Clean

if %errorlevel% eql 0 (
    echo.
    echo Build completed successfully!
    echo Check the 'dist' folder for the executable files.
) else (
    echo.
    echo Build failed. Check the error messages above.
)

echo.
pause
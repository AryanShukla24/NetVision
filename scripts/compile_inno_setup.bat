@echo off
setlocal
echo ======================================================================
echo NetVision - Inno Setup Compiler Helper
echo ======================================================================

set "ISCC_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if "%ISCC_PATH%"=="" (
    where iscc >nul 2>nul
    if %errorlevel% equ 0 set "ISCC_PATH=iscc"
)

if "%ISCC_PATH%"=="" (
    echo [ERROR] Inno Setup 6 compiler (iscc.exe) was not found on your system.
    echo Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
    echo or use scripts\build_installer.bat to generate NetVision_Setup.exe directly.
    pause
    exit /b 1
)

echo [INFO] Found Inno Setup compiler: %ISCC_PATH%
echo [INFO] Compiling installer\NetVision_Setup.iss...
"%ISCC_PATH%" "%~dp0..\installer\NetVision_Setup.iss"

if %errorlevel% neq 0 (
    echo [ERROR] Inno Setup compilation failed.
    pause
    exit /b %errorlevel%
)

echo [SUCCESS] Inno Setup installer compiled successfully to installer\NetVision_Setup_Inno.exe
pause

@echo off
setlocal
cd /d "%~dp0.."

echo ======================================================================
echo NetVision - Installer Build Script
echo ======================================================================

set "PYTHON_EXE="
if exist "venv\Scripts\python.exe" set "PYTHON_EXE=venv\Scripts\python.exe"
if "%PYTHON_EXE%"=="" (
    where py >nul 2>nul
    if %errorlevel% equ 0 set "PYTHON_EXE=py -3"
)
if "%PYTHON_EXE%"=="" (
    where python >nul 2>nul
    if %errorlevel% equ 0 set "PYTHON_EXE=python"
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python interpreter not found!
    pause
    exit /b 1
)

echo [INFO] Using Python: %PYTHON_EXE%
%PYTHON_EXE% scripts\build_installer.py
if %errorlevel% neq 0 (
    echo [ERROR] Installer build failed!
    pause
    exit /b %errorlevel%
)

echo [SUCCESS] NetVision_Setup.exe built successfully in installer\
pause

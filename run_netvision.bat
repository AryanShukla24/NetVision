@echo off
setlocal enabledelayedexpansion
title NetVision - Smart Network Quality & Wi-Fi Analyzer

cd /d "%~dp0"

echo ======================================================================
echo           NetVision - Smart Network Quality & Wi-Fi Analyzer
echo               BTech Computer Science Academic Project
echo ======================================================================
echo.

:: 1. Locate System Python
set "PYTHON_CMD="

:: Check 'py -3'
py -3 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3"
    goto :PYTHON_FOUND
)

:: Check 'python'
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=python"
    goto :PYTHON_FOUND
)

:: Check uv python in AppData
if exist "%APPDATA%\uv\python\cpython-3.12-windows-x86_64-none\python.exe" (
    set "PYTHON_CMD=%APPDATA%\uv\python\cpython-3.12-windows-x86_64-none\python.exe"
    goto :PYTHON_FOUND
)

:: Check LocalAppData Python
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_CMD=%%D\python.exe"
        goto :PYTHON_FOUND
    )
)

:: Check Program Files Python
for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_CMD=%%D\python.exe"
        goto :PYTHON_FOUND
    )
)

:PYTHON_NOT_FOUND
echo [ERROR] Python 3 was not detected on this system.
echo.
echo NetVision requires Python 3.9 or newer.
echo Please install Python from https://www.python.org/downloads/
echo Make sure to check the box "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:PYTHON_FOUND
:: 2. Verify Python version is >= 3.9
%PYTHON_CMD% -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Detected Python is older than 3.9.
    echo NetVision requires Python 3.9 or newer.
    echo.
    pause
    exit /b 1
)

:: 3. Validate or Create Virtual Environment
set "VENV_DIR=%~dp0venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "NEED_VENV=0"

if not exist "%VENV_PYTHON%" (
    set "NEED_VENV=1"
) else (
    :: Test whether venv's python executable actually works
    "%VENV_PYTHON%" -c "import sys" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [WARNING] Existing virtual environment is invalid or points to another computer.
        echo Removing broken virtual environment...
        rmdir /s /q "%VENV_DIR%" >nul 2>&1
        set "NEED_VENV=1"
    )
)

if "!NEED_VENV!"=="1" (
    echo [SETUP] Creating fresh virtual environment in venv\...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        echo Please ensure you have write permissions in this folder.
        echo.
        pause
        exit /b 1
    )
    echo [SETUP] Virtual environment created successfully.
)

:: 4. Verify / Install Dependencies
"%VENV_PYTHON%" -c "import PySide6, matplotlib, pandas, numpy, reportlab, requests" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [SETUP] Installing required runtime dependencies from requirements.txt...
    "%VENV_PYTHON%" -m pip install --upgrade pip
    "%VENV_PYTHON%" -m pip install -r "%~dp0requirements.txt"
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Dependency installation failed.
        echo Please check your internet connection and try running:
        echo   "%VENV_PYTHON%" -m pip install -r "%~dp0requirements.txt"
        echo.
        pause
        exit /b 1
    )
    echo [SETUP] Dependencies successfully installed.
)

:: 5. Launch NetVision
echo [START] Launching NetVision...
"%VENV_PYTHON%" "%~dp0main.py"
set "APP_EXIT_CODE=%ERRORLEVEL%"

if %APP_EXIT_CODE% NEQ 0 (
    echo.
    echo [NOTICE] NetVision exited with code %APP_EXIT_CODE%.
    pause
)

exit /b %APP_EXIT_CODE%

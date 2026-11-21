@echo off
setlocal
cd /d "%~dp0\.."
title NetVision - Windows Executable Builder

echo ======================================================================
echo             NetVision - Windows Executable Builder (PyInstaller)
echo ======================================================================
echo.

set "PYTHON_EXE=%~dp0..\venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Virtual environment python not found at %PYTHON_EXE%
    echo Please run run_netvision.bat first to set up the environment.
    pause
    exit /b 1
)

"%PYTHON_EXE%" "%~dp0build_exe.py"
set "BUILD_EXIT_CODE=%ERRORLEVEL%"

if %BUILD_EXIT_CODE% EQU 0 (
    echo.
    echo [SUCCESS] NetVision build completed successfully!
    echo Output directory: %~dp0..\dist\NetVision\
) else (
    echo.
    echo [ERROR] Build failed with exit code %BUILD_EXIT_CODE%.
)

pause
exit /b %BUILD_EXIT_CODE%

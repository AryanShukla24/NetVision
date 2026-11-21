@echo off
setlocal enabledelayedexpansion
title NetVision - Automated Test Suite

cd /d "%~dp0"

echo ======================================================================
echo           NetVision - Automated Test Suite Execution
echo ======================================================================
echo.

set "VENV_DIR=%~dp0venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo [SETUP] Virtual environment not found. Running launcher first to set up...
    call "%~dp0run_netvision.bat"
)

:: Ensure pytest is installed
"%VENV_PYTHON%" -c "import pytest" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [SETUP] Installing test dependencies from requirements-dev.txt...
    "%VENV_PYTHON%" -m pip install -r "%~dp0requirements-dev.txt"
)

echo [TEST] Executing pytest on tests/ ...
"%VENV_PYTHON%" -m pytest tests\ -v %*
set "TEST_EXIT_CODE=%ERRORLEVEL%"

echo.
if %TEST_EXIT_CODE% EQU 0 (
    echo [SUCCESS] All automated tests passed.
) else (
    echo [FAILURE] Some tests failed with exit code %TEST_EXIT_CODE%.
)
echo.
pause
exit /b %TEST_EXIT_CODE%

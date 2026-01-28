@echo off
echo ================================================================
echo       WORK COMPUTER POLLER - Start Script
echo ================================================================
echo.
echo This script will:
echo   1. Start polling Google Drive for automation commands
echo   2. Run local automation when commands are found
echo   3. Report results back to Telegram bot
echo.
echo Keep this window open while polling!
echo Press Ctrl+C to stop the poller.
echo.
echo ================================================================
echo.

cd /d "%~dp0"

echo [INFO] Using Python from Project_Organization folder...
set PYTHON_EXE=Z:\AAA-Mohammad Khair AbuShanab\ULTIMATE_BACKUP_FOLDER\Project_Organization\Python\python.exe

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python not found at: %PYTHON_EXE%
    echo.
    pause
    exit /b 1
)

echo [INFO] Starting work computer poller...
echo.

"%PYTHON_EXE%" work_computer_poller.py

echo.
echo [INFO] Poller stopped.
pause

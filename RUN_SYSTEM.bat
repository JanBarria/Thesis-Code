@echo off
REM Batch file to run the Chaos-Based Secure Communication System
REM Double-click this file to start the interactive menu

echo.
echo ========================================================================
echo   CHAOS-BASED SECURE COMMUNICATION SYSTEM
echo   De La Salle University - ECE Thesis Project
echo ========================================================================
echo.
echo Starting interactive menu...
echo.

REM Run the Python script
python run_system.py

REM Pause if there was an error
if errorlevel 1 (
    echo.
    echo ========================================================================
    echo   ERROR: Failed to run the system
    echo ========================================================================
    echo.
    echo Possible issues:
    echo   1. Python is not installed or not in PATH
    echo   2. Required packages are not installed
    echo   3. Script file is missing
    echo.
    echo To fix:
    echo   1. Install Python 3.x from python.org
    echo   2. Run: pip install numpy scipy soundfile
    echo   3. Ensure run_system.py exists in this directory
    echo.
    pause
)

@REM Made with Bob

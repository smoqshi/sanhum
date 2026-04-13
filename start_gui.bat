@echo off
echo ========================================
echo Sanhum Robot GUI - Quick Start
echo ========================================
echo.
echo Starting Python GUI without installation...
echo.

REM Change to project directory
cd /d "%~dp0"

REM Add src directory to Python path
set PYTHONPATH=%PYTHONPATH%;%~dp0\src

REM Start GUI
echo Starting GUI...
python src\gui_main.py

echo.
echo GUI stopped. Press any key to exit...
pause >nul

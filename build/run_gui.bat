@echo off
echo Sanhum Robot GUI Launcher
echo ========================
echo.

REM Try to find Python GUI
echo Looking for Python GUI files...

REM Check if we can run Python directly
cd /d "C:\Users\smoqshi\sanhum"

REM Try to run GUI directly with Python
echo Attempting to start GUI with Python...
python src/gui_main.py 2>nul
if errorlevel 1 (
    echo GUI Python script not found, trying alternative...
    
    REM Try to find any Python GUI file
    if exist "src\*.py" (
        echo Found Python files in src directory
        dir /b src\*.py
        echo.
        echo You may need to run the GUI manually:
        echo   python src\[filename].py
    ) else (
        echo No Python GUI files found
    )
)

echo.
echo If GUI didn't start, you may need to:
echo 1. Install missing dependencies
echo 2. Check ROS2 installation
echo 3. Run: python scripts\check_dependencies.py
echo.
pause

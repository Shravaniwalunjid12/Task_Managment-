@echo off
title TaskFlow - Django Server
color 0A

echo.
echo  ==========================================
echo    TaskFlow - Task Management System
echo  ==========================================
echo.

cd /d "%~dp0"

echo  [Step 1/4] Checking Python...
python --version
if errorlevel 1 (
    echo  ERROR: Python not found! Please install Python first.
    pause
    exit
)

echo  [Step 2/4] Setting up virtual environment...
if not exist venv (
    python -m venv venv
    echo  Virtual environment created.
) else (
    echo  Virtual environment found.
)

echo  [Step 3/4] Activating and installing packages...
call venv\Scripts\activate
pip install django pillow --quiet

echo  [Step 4/4] Starting server...
python manage.py migrate --run-syncdb
echo.
echo  ==========================================
echo    Server is running!
echo    Open browser: http://127.0.0.1:8000/
echo.
echo    Admin login:  admin    / admin123
echo    User login:   testuser / user123
echo.
echo    Press Ctrl+C to stop the server
echo  ==========================================
echo.

python manage.py runserver

pause

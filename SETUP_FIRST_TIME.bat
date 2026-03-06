@echo off
title TaskFlow - First Time Setup
color 0B

echo.
echo  ==========================================
echo    TaskFlow - First Time Setup
echo    Run this ONCE when starting fresh
echo  ==========================================
echo.

cd /d "%~dp0"

echo  [1/5] Creating virtual environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate

echo  [2/5] Installing packages...
pip install django pillow --quiet

echo  [3/5] Running database migrations...
python manage.py migrate

echo  [4/5] Creating demo users and tasks...
python setup_demo.py

echo  [5/5] Done!
echo.
echo  ==========================================
echo    Setup Complete!
echo    Now double-click START_SERVER.bat
echo.
echo    Admin:  admin    / admin123
echo    User:   testuser / user123
echo  ==========================================
echo.
pause

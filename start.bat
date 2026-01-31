@echo off
echo ========================================
echo    Video Content Management System
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Check if .env exists
if not exist ".env" (
    echo.
    echo ================================================
    echo  IMPORTANT: Email Configuration Required
    echo ================================================
    echo  Copy .env.example to .env and configure:
    echo  - SMTP_SERVER (e.g., smtp.gmail.com)
    echo  - SMTP_PORT (e.g., 587)
    echo  - SMTP_EMAIL (your email)
    echo  - SMTP_PASSWORD (your app password)
    echo ================================================
    echo.
    copy .env.example .env
)

echo.
echo Starting the application...
echo.
echo ========================================
echo  Dashboard: http://127.0.0.1:5000
echo  Calendar:  http://127.0.0.1:5000/calendar
echo  Teams:     http://127.0.0.1:5000/teams
echo  Schedule:  http://127.0.0.1:5000/schedule
echo ========================================
echo.

python app.py

pause

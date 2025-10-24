@echo off
echo ============================================
echo   Bid Management System - Starting...
echo ============================================
echo.

REM Check if virtual environment exists
if not exist ".venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if database exists
if not exist "database.xlsx" (
    echo Database not found. Creating database...
    .venv\Scripts\python.exe create_database.py
    echo.
)

echo Starting Flask application...
echo.
echo Open your browser to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ============================================
echo.

.venv\Scripts\python.exe app.py

pause

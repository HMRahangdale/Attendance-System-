@echo off
REM Run the attendance system with environment variables from .env
cd /d "%~dp0"
IF NOT EXIST ".env" (
  echo Please create a .env file first by copying .env.example and updating it.
  pause
  exit /b 1
)
"%~dp0\.venv\Scripts\python.exe" app.py

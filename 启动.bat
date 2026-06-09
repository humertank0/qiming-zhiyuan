@echo off
title 雪峰Agent
cd /d "%~dp0"

if not exist ".env" (
    echo .env not found!
    echo Copy .env.example to .env and fill in your API key.
    pause
    exit /b 1
)

echo Starting...
C:\Users\17625\AppData\Local\Programs\Python\Python312\python.exe agent.py 2>&1
echo.
pause

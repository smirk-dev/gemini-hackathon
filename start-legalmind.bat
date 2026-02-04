@echo off
REM LegalMind Project Startup Script
REM Start both backend and frontend services

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo LegalMind - Legal Contract Analysis Platform
echo ============================================================
echo.

REM Check if we're in the right directory
if not exist "backend" (
    echo ERROR: Please run this script from the project root directory
    echo (where you see 'backend' and 'frontend' folders)
    pause
    exit /b 1
)

if not exist "frontend" (
    echo ERROR: Frontend folder not found!
    pause
    exit /b 1
)

echo Starting services...
echo.

REM Start backend
echo [1/2] Starting Backend API (port 8000)...
start "LegalMind Backend" cmd /k "cd /d "!cd!\backend" && python main_new.py"
timeout /t 3 /nobreak

REM Start frontend
echo [2/2] Starting Frontend (port 3000)...
start "LegalMind Frontend" cmd /k "cd /d "!cd!\frontend" && npm run dev"
timeout /t 3 /nobreak

echo.
echo ============================================================
echo Services Starting...
echo ============================================================
echo.
echo ✓ Backend API:     http://localhost:8000
echo ✓ Frontend:        http://localhost:3000
echo ✓ API Docs:        http://localhost:8000/docs
echo.
echo Waiting for services to initialize...
echo.

timeout /t 5 /nobreak

echo.
echo ============================================================
echo Opening Frontend...
echo ============================================================
echo.

start http://localhost:3000

echo.
echo ✓ LegalMind is ready!
echo.
echo Access the application at: http://localhost:3000
echo.
pause

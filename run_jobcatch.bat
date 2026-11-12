@echo off
title JobCatch AI - US Candidate Portal
echo ========================================================
echo   DEMARRAGE DE JOBCATCH AI (Port: 8080)
echo ========================================================
echo.
echo [INFO] Ouverture de JobCatch AI...
echo [INFO] Accedez a : http://localhost:8080
echo.
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" -m uvicorn jobcatch.main:app --host 127.0.0.1 --port 8080 --reload
) else if exist "C:\Users\levis\Documents\SAAS20017\venv\Scripts\python.exe" (
    "C:\Users\levis\Documents\SAAS20017\venv\Scripts\python.exe" -m uvicorn jobcatch.main:app --host 127.0.0.1 --port 8080 --reload
) else (
    python -m uvicorn jobcatch.main:app --host 127.0.0.1 --port 8080 --reload
)
pause

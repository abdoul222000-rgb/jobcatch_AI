@echo off
title Push JobCatch AI to GitHub
echo ========================================================
echo   ENVOI DE JOBCATCH AI VERS GITHUB (abdoul222000-rgb)
echo ========================================================
echo.
cd /d "%~dp0"

:: Detection automatique du chemin exact de Git
set "GIT_CMD=git"
if exist "C:\Users\levis\AppData\Local\Programs\Git\cmd\git.exe" (
    set "GIT_CMD=C:\Users\levis\AppData\Local\Programs\Git\cmd\git.exe"
) else if exist "C:\Program Files\Git\cmd\git.exe" (
    set "GIT_CMD=C:\Program Files\Git\cmd\git.exe"
) else if exist "C:\Program Files (x86)\Git\cmd\git.exe" (
    set "GIT_CMD=C:\Program Files (x86)\Git\cmd\git.exe"
)

echo [INFO] Git detecte : "%GIT_CMD%"
echo.

echo [1/4] Configuration du depot GitHub...
"%GIT_CMD%" remote remove origin 2>nul
"%GIT_CMD%" remote add origin https://github.com/abdoul222000-rgb/jobcatch_AI.git

echo [2/4] Ajout des fichiers...
"%GIT_CMD%" add .

echo [3/4] Enregistrement du commit...
"%GIT_CMD%" commit -m "feat: complete JobCatch AI with credit card trial auto-rebill and Render config"

echo [4/4] Envoi vers GitHub (branche main)...
"%GIT_CMD%" branch -M main
"%GIT_CMD%" push -u origin main

echo.
echo ========================================================
echo   CODE ENVOYE AVEC SUCCES SUR GITHUB !
echo ========================================================
pause

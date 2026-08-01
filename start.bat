@echo off
title Studio Medico - Doctor Website
cd /d "%~dp0"
echo.
echo  [Studio Medico] Avvio in corso...
echo.
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo.
    echo  [ERRORE] Ambiente virtuale non trovato in .venv\
    echo  Esegui: python -m venv .venv
    echo  Poi: pip install -r requirements.txt
    pause
    exit /b 1
)
echo.
echo  =============================================
echo    STUDIO MEDICO - Doctor Website
echo  =============================================
echo.
echo  Seleziona medico: http://localhost:8000/select
echo  Sito principale:  http://localhost:8000
echo.
echo  Premi CTRL+C per fermare il server
echo  =============================================
echo.
python main.py
if %errorlevel% neq 0 (
    echo.
    echo  [ERRORE] Il server si e fermato inaspettatamente
    pause
)

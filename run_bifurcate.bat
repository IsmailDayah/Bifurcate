@echo off
title Bifurcate console
cd /d "%~dp0"

rem Prefer the project venv; fall back to system python.
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

rem Self-heal: if any dependency is missing, install the pinned set once.
"%PY%" -c "import streamlit, cryptography, plotly, PIL, numpy" 2>nul
if errorlevel 1 (
    echo First run - installing dependencies...
    "%PY%" -m pip install -r requirements.txt
)

echo Starting Bifurcate... the browser will open automatically.
"%PY%" -m streamlit run app/Home.py --server.headless=false
pause

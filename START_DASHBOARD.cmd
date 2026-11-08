@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto check_packages
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo Python 3.12 is required. Install it from https://www.python.org/downloads/ then try again.
  pause
  exit /b 1
)
py -3.12 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
:check_packages
".venv\Scripts\python.exe" -c "import streamlit, pandas, numpy, pyarrow, plotly" >nul 2>&1
if errorlevel 1 (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto failed
)
if /i "%~1"=="--check" (
  echo AceIQ Python environment is ready.
  exit /b 0
)
echo Keep this window open while using AceIQ. Press Ctrl+C to stop.
echo Dashboard address: http://127.0.0.1:8501
echo Floor lab address: http://127.0.0.1:8502/floor-lab
".venv\Scripts\python.exe" run_local.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo Startup failed. See the error above and JUDGE_START_HERE.md.
pause
exit /b 1

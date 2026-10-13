@echo off
setlocal
if not exist .venv\Scripts\python.exe (
  echo First install Python 3.11+ and run setup_windows.bat.
  pause
  exit /b 1
)
.venv\Scripts\python.exe run_aethersort.py

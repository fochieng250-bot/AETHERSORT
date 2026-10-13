@echo off
setlocal
py -3 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo.
echo Setup complete. Double-click LAUNCH_WINDOWS.bat to start AetherSort.
pause
exit /b 0
:fail
echo Setup failed. Check that Python 3.11+ is installed and available via the py launcher.
pause
exit /b 1

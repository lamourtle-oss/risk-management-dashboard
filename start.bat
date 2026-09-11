@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install -r pipeline\requirements.txt
)
".venv\Scripts\python.exe" pipeline\run.py
if errorlevel 1 exit /b 1
echo.
echo Open http://127.0.0.1:8080
echo Default password: Risk2026
".venv\Scripts\python.exe" pipeline\serve.py 8080

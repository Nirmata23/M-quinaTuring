@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Turing Bricks
where python >nul 2>nul
if errorlevel 1 (
  echo No encontre Python. Instala Python 3.12 desde https://www.python.org/downloads/
  echo y marca la casilla "Add python.exe to PATH" durante la instalacion.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Preparando el entorno por primera vez, espera un momento...
  python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 pause

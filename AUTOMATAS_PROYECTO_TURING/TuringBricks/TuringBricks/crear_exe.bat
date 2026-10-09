@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Crear TuringBricks.exe
where python >nul 2>nul
if errorlevel 1 (
  echo No encontre Python. Instala Python 3.12 desde https://www.python.org/downloads/
  echo y marca la casilla "Add python.exe to PATH" durante la instalacion.
  pause
  exit /b 1
)
echo [1/3] Creando entorno limpio...
if not exist ".venv-build\Scripts\python.exe" python -m venv .venv-build
echo [2/3] Instalando dependencias...
".venv-build\Scripts\python.exe" -m pip install --upgrade pip
".venv-build\Scripts\python.exe" -m pip install -r requirements-dev.txt
echo [3/3] Creando el ejecutable (tarda unos minutos)...
".venv-build\Scripts\python.exe" -m PyInstaller --noconfirm --clean TuringBricks.spec
if errorlevel 1 (
  echo Hubo un error al crear el ejecutable.
  pause
  exit /b 1
)
echo.
echo Listo. Tu programa esta en:  dist\TuringBricks\TuringBricks.exe
echo Para compartirlo, comprime la carpeta completa dist\TuringBricks
explorer dist\TuringBricks
pause

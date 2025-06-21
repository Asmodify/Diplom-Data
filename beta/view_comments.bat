@echo off
cd /d "%~dp0"
title Facebook Comments Viewer
echo Facebook Comments Viewer
echo ===================================

if not exist ".venv\Scripts\activate.bat" (
    echo Setting up virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    pip install tabulate pandas --upgrade
) else (
    call .venv\Scripts\activate.bat
    echo Ensuring all dependencies are up to date...
    pip install tabulate pandas --upgrade
)

python view_comments.py

pause

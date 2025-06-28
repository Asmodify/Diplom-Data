@echo off
cd /d "%~dp0"
title Facebook Scraper - Manual Login Mode
echo Facebook Scraper - MANUAL LOGIN MODE
echo ===================================

REM Install core dependencies first
pip install sqlalchemy==2.0.17 pandas tabulate webdriver-manager selenium --upgrade

if not exist ".venv\Scripts\activate.bat" (
    echo Setting up virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    pip install webdriver-manager selenium --upgrade
) else (
    call .venv\Scripts\activate.bat
    echo Ensuring all dependencies are up to date...
    pip install sqlalchemy==2.0.17 webdriver-manager selenium pandas tabulate --upgrade
)

echo.
echo Running Facebook scraper with MANUAL LOGIN...
python manual_login.py --pages-file pages.txt --max-posts 10 --wait-time 300
if %ERRORLEVEL% NEQ 0 (
    echo Scraping failed!
    pause
    exit /b 1
)

echo.
echo Done! Check the 'images' folder for downloaded images.
pause

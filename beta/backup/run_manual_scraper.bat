@echo off
cd /d "%~dp0"
title Facebook Scraper - Manual Login Mode
cls

echo ================================================================================
echo                      FACEBOOK SCRAPER WITH MANUAL LOGIN
echo ================================================================================
echo.
echo This script will run the Facebook scraper with manual login.
echo A Firefox browser will open where you need to log in to Facebook.
echo.
echo IMPORTANT STEPS:
echo   1. When the browser opens, log in with your Facebook credentials
echo   2. Complete any security checks if prompted
echo   3. Once logged in, type "done" in the terminal prompt
echo.
echo ================================================================================
echo.
pause

REM Set up environment
if not exist ".venv\Scripts\activate.bat" (
    echo Setting up virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

REM Run the test_connection script first
python test_postgres_connection.py
if %ERRORLEVEL% NEQ 0 (
    echo Database connection failed! Please check your database settings.
    pause
    exit /b 1
)

REM Run the scraper with a single page first as a test
echo.
echo Starting Facebook scraper with manual login...
echo.
python facebook_scraper_all.py --pages eaglenewssocial --max-posts 1
if %ERRORLEVEL% NEQ 0 (
    echo Initial scraping failed. Please check the error messages above.
    pause
    exit /b 1
)

REM If successful, ask if user wants to scrape more pages
echo.
echo First page successfully scraped! Do you want to scrape more pages from pages.txt?
echo.
set /p continue="Continue scraping more pages? (y/n): "

if /i "%continue%"=="y" (
    echo.
    echo Running full scraper for all pages...
    python facebook_scraper_all.py --pages-file pages.txt --max-posts 5
)

echo.
echo Scraping completed. Check the images/ folder for downloaded content.
pause
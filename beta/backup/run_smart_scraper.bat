@echo off
cd /d "%~dp0"
title Facebook Smart Scraper
echo ====================================
echo Facebook Smart Scraper
echo ====================================
echo This script runs the improved Facebook scraper with smart features.
echo.
echo Features:
echo - Automatic screenshot capture of posts
echo - Smart comment detection (analyzes if posts have comments)
echo - Comment extraction with intelligent handling:
echo   * Navigates to post page for comments
echo   * Extracts all comments and replies 
echo   * Limits to 50 comments if post has more than 100
echo - Post image downloading
echo - Manual login support
echo.

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
)

echo.
echo Running smart Facebook scraper...
python facebook_scraper_all.py --pages-file pages.txt --max-comments 50

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo There was an error during scraping. Check the logs for details.
) else (
    echo.
    echo Scraping completed successfully!
    echo.
    echo Check the following locations for results:
    echo - images/            : Downloaded post images and screenshots
    echo - facebook_scraper.db: Database with all extracted data
)

echo.
pause

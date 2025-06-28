@echo off
cd /d "%~dp0"
title Facebook Complete Scraper
echo Facebook Complete Scraper
echo ===================================

REM Create necessary directories
if not exist "exports" mkdir exports
if not exist "images" mkdir images
if not exist "logs" mkdir logs
if not exist "debug" mkdir debug

REM Check for virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo Setting up virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    pip install tabulate pandas webdriver-manager selenium dateparser requests Pillow --upgrade
) else (
    call .venv\Scripts\activate.bat
    echo Ensuring all dependencies are up to date...
    pip install tabulate pandas webdriver-manager selenium dateparser requests Pillow --upgrade
)

echo.
echo Initializing project...
python init_project.py
if %ERRORLEVEL% NEQ 0 (
    echo Project initialization failed!
    pause
    exit /b 1
)

echo.
echo === Facebook Scraper Options ===
echo.
echo 1. Scrape all with defaults (all posts, images, comments)
echo 2. Limit posts (specify max posts per page)
echo 3. Skip images (scrape posts and comments only)
echo 4. Skip comments (scrape posts and images only)
echo 5. Custom options
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Running full scraper with default options...
    python facebook_scraper_all.py --pages-file pages.txt
) else if "%choice%"=="2" (    set /p maxposts="Enter maximum posts per page: "
    echo Running scraper with max %maxposts% posts per page...
    python facebook_scraper_all.py --pages-file pages.txt --max-posts %maxposts%
) else if "%choice%"=="3" (
    echo Running scraper without images...
    python facebook_scraper_all.py --pages-file pages.txt --no-images
) else if "%choice%"=="4" (
    echo Running scraper without comments...
    python facebook_scraper_all.py --pages-file pages.txt --no-comments
) else if "%choice%"=="5" (
    echo Custom options selected.    set /p maxposts="Enter maximum posts per page (press Enter for no limit): "
    
    set /p skipoption="Skip images? (y/n): "
    if /i "%skipoption%"=="y" (
        set skipimages=--no-images
    ) else (
        set skipimages=
    )
    
    set /p skipoption="Skip comments? (y/n): "
    if /i "%skipoption%"=="y" (
        set skipcomments=--no-comments
    ) else (
        set skipcomments=
    )
    
    if not "%maxposts%"=="" (
        echo Running scraper with custom options...
        python facebook_scraper_all.py --pages-file pages.txt --max-posts %maxposts% %skipimages% %skipcomments%
    ) else (
        echo Running scraper with custom options...
        python facebook_scraper_all.py --pages-file pages.txt %skipimages% %skipcomments%
    )
) else (
    echo Invalid choice! Using default options...
    python facebook_scraper_all.py --pages-file pages.txt
)

if %ERRORLEVEL% NEQ 0 (
    echo Scraping failed!
    pause
    exit /b 1
)

echo.
echo Scraping completed!
echo.
echo Would you like to view the scraped comments now?
set /p viewcomments="View comments? (y/n): "

if /i "%viewcomments%"=="y" (
    echo Starting comments viewer...
    python view_comments.py
)

echo.
echo Done! All data has been saved to the database.
echo You can view comments anytime by running view_comments.bat
pause

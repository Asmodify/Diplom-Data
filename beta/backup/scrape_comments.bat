@echo off
cd /d "%~dp0"
title Facebook Comment Scraper
cls

REM ============================================
echo.
echo   FACEBOOK COMMENT SCRAPER - ENHANCED VERSION
echo   ==========================================
echo.
echo   This tool scrapes ALL comments from Facebook posts
echo   You will need to log in manually when the browser opens
echo.
echo   Options:
echo     1. Scrape most recent posts (up to 20)
echo     2. Scrape specific post IDs
echo     3. Scrape more posts (up to 50)
echo     4. Run in headless mode (no browser visible)
echo     q. Quit
echo.
REM ============================================

REM Install dependencies if needed
if not exist ".venv\Scripts\activate.bat" (
    echo Setting up virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    pip install webdriver-manager selenium --upgrade
) else (
    call .venv\Scripts\activate.bat
)

REM First-time setup for Firefox
if not exist "%LOCALAPPDATA%\Mozilla\Firefox\Profiles" (
    echo Setting up Firefox for first use...
    echo This will open Firefox briefly to create a profile.
    start firefox -CreateProfile "facebook_scraper %LOCALAPPDATA%\Mozilla\Firefox\Profiles\facebook_scraper"
    timeout /t 3 /nobreak >nul
)

:MENU_LOOP
set choice=
set /p choice="Select an option (1-4, q): "

if "%choice%"=="1" (
    echo.
    echo Running Facebook Comment Scraper...
    python comment_scraper.py
    goto END
)

if "%choice%"=="2" (
    echo.
    echo Please enter post IDs separated by spaces:
    echo Example: 123456789 987654321
    echo.
    set /p post_ids="Post IDs: "
    echo.
    echo Running Facebook Comment Scraper for specific posts...
    python comment_scraper.py --post-ids %post_ids%
    goto END
)

if "%choice%"=="3" (
    echo.
    echo Running Facebook Comment Scraper for more posts (up to 50)...
    python comment_scraper.py --limit 50
    goto END
)

if "%choice%"=="4" (
    echo.
    echo Running Facebook Comment Scraper in headless mode...
    python comment_scraper.py --headless
    goto END
)

if "%choice%"=="q" (
    echo Exiting...
    exit /b 0
)

echo.
echo Invalid choice, please try again.
goto MENU_LOOP

:END
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Scraping failed! Check the logs for more details.
    echo Logs are located in the logs/ directory.
) else (
    echo.
    echo All comments scraped successfully!
    echo You can view them using the view_comments.bat tool.
)

pause
exit /b %ERRORLEVEL%

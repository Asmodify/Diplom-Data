@echo off
cd /d "%~dp0"
echo ================================================================================
echo                      FACEBOOK SMART SCRAPER
echo ================================================================================

REM Install requirements if needed
python -m pip install -r requirements.txt

echo.
echo Starting Facebook scraper...
echo Options:
echo - Max comments per post: 100 (override with --max-comments)
echo - Saves screenshots (disable with --no-screenshots)
echo - Downloads images (disable with --no-images)
echo - Manual login required
echo.
echo Additional options:
echo --headless            Run without browser UI
echo --pages FILE         Use custom pages file
echo --max-comments N     Set maximum comments per post
echo --no-screenshots    Disable post screenshots
echo --no-images        Disable image downloads
echo.
echo IMPORTANT: You will need to log in manually when the browser opens
echo.
pause

python -m automation.auto_scraper %*

if %ERRORLEVEL% NEQ 0 (
    echo Error running scraper! Check the logs for details.
    pause
    exit /b 1
)

echo.
echo Scraping completed successfully!
pause

echo.
echo Scraping completed! Check the following folders:
echo - screenshots/: Post screenshots
echo - images/: Downloaded images
echo - exports/: Post data and comments
echo.
pause

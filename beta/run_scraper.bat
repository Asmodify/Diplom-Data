@echo off
cd /d "%~dp0"
echo Facebook Scraper - MANUAL LOGIN MODE
echo ===================================

if not exist ".venv\Scripts\activate.bat" (
    echo Setting up virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    pip install webdriver-manager selenium --upgrade
) else (
    call .venv\Scripts\activate.bat
    echo Ensuring all dependencies are up to date...
    pip install -r requirements.txt
    pip install webdriver-manager selenium --upgrade
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
echo Running Facebook scraper with MANUAL LOGIN...
echo ===================================
echo IMPORTANT INSTRUCTIONS:
echo 1. A Firefox browser will open to Facebook's login page
echo 2. Log in with your Facebook credentials
echo 3. Return to this terminal window after logging in
echo 4. Type 'done' and press Enter when logged in
echo 5. OR wait for automatic login detection (up to 5 minutes)
echo ===================================
python scraper_cli.py --pages-file pages.txt --max-posts 5 --manual
if %ERRORLEVEL% NEQ 0 (
    echo Scraping failed!
    pause
    exit /b 1
)

echo.
echo Checking scraped data...
python check_db.py
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Database check failed
)

echo.
echo Done! Check the 'images' folder for downloaded real images.
pause

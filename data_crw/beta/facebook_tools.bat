@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
title Facebook Scraper Toolkit

REM Set Python path to include project root
set "PYTHONPATH=%~dp0;%~dp0scraper;%~dp0automation;%~dp0content_manager;%~dp0utils;%~dp0db"

REM Check Python installation
python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Setup virtual environment if needed
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Error creating virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/upgrade pip and requirements if needed
python -m pip install --upgrade pip > nul
if not exist "requirements.txt" (
    echo Error: requirements.txt not found
    pause
    exit /b 1
)

REM Check if requirements need to be installed
python -c "import selenium" > nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error installing requirements
        pause
        exit /b 1
    )
)

:MAIN_MENU
cls
echo.
echo   FACEBOOK SCRAPER TOOLKIT
echo   =====================
echo.
echo   1. Initialize Project (first-time setup)
echo   2. Test Database Connection
echo   3. Configure Database
echo   4. Run Scraper
echo   5. View Content Manager
echo   6. Export Data
echo   7. Utilities
echo   q. Quit
echo.

set choice=
set /p choice="Select an option (1-7, q): "

if "%choice%"=="1" (
    call :INIT_PROJECT
) else if "%choice%"=="2" (
    call :TEST_CONNECTION
) else if "%choice%"=="3" (
    call :CONFIGURE_DATABASE
) else if "%choice%"=="4" (
    call :RUN_SCRAPER
) else if "%choice%"=="5" (
    call :CONTENT_MANAGER
) else if "%choice%"=="6" (
    call :EXPORT_DATA
) else if "%choice%"=="7" (
    call :UTILITIES
) else if /I "%choice%"=="q" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice
    timeout /t 2 > nul
    goto MAIN_MENU
)
goto MAIN_MENU

:INIT_PROJECT
cls
echo.
echo   PROJECT INITIALIZATION
echo   =====================
echo.
echo   This will set up required folders and database.
echo   Make sure PostgreSQL is running and configured.
echo.
echo   Options:
echo   1. Standard initialization
echo   2. Reset database (WARNING: Deletes all data)
echo   3. Back to main menu
echo.
set init_choice=
set /p init_choice="Select an option (1-3): "

if "!init_choice!"=="1" (
    python setup\init_project.py
) else if "!init_choice!"=="2" (
    echo WARNING: This will delete all data! Type 'RESET' to confirm:
    set confirm=
    set /p confirm="> "
    if "!confirm!"=="RESET" (
        python setup\init_project.py --reset
    )
)
pause
goto :eof

:TEST_CONNECTION
cls
echo.
echo   DATABASE CONNECTION TEST
echo   =======================
echo.
python tests\test_postgres_connection.py
pause
goto :eof

:CONFIGURE_DATABASE
cls
echo.
echo   DATABASE CONFIGURATION
echo   =====================
echo.
echo   1. Configure PostgreSQL connection
echo   2. View current configuration
echo   3. Back to main menu
echo.
set db_choice=
set /p db_choice="Select an option (1-3): "

if "!db_choice!"=="1" (
    call setup\setup_postgres.bat
) else if "!db_choice!"=="2" (
    python db\show_config.py
)
pause
goto :eof

:RUN_SCRAPER
cls
echo.
echo   FACEBOOK SCRAPER
echo   ===============
echo.
echo   1. Run scraper (default settings)
echo   2. Run scraper (headless mode)
echo   3. Run scraper (custom options)
echo   4. Back to main menu
echo.
set scrape_choice=
set /p scrape_choice="Select an option (1-4): "

if "!scrape_choice!"=="1" (
    python automation\auto_scraper.py
) else if "!scrape_choice!"=="2" (
    python automation\auto_scraper.py --headless
) else if "!scrape_choice!"=="3" (
    echo.
    echo Available options:
    echo   --headless         Run without browser UI
    echo   --max-comments N   Limit comments per post
    echo   --no-screenshots   Disable screenshots
    echo   --no-images       Disable image downloads
    echo.
    set options=
    set /p options="Enter options: "
    python automation\auto_scraper.py !options!
)
pause
goto :eof

:CONTENT_MANAGER
cls
echo.
echo   CONTENT MANAGER
echo   ==============
echo.
echo   1. View all content
echo   2. Search content
echo   3. Filter by date
echo   4. Back to main menu
echo.
set content_choice=
set /p content_choice="Select an option (1-4): "

if "!content_choice!"=="1" (
    python content_manager\content_manager.py --view-all
) else if "!content_choice!"=="2" (
    set search_term=
    set /p search_term="Enter search term: "
    python content_manager\content_manager.py --search "!search_term!"
) else if "!content_choice!"=="3" (
    set start_date=
    set /p start_date="Enter start date (YYYY-MM-DD): "
    set end_date=
    set /p end_date="Enter end date (YYYY-MM-DD): "
    python content_manager\content_manager.py --date-range "!start_date!" "!end_date!"
)
pause
goto :eof

:EXPORT_DATA
cls
echo.
echo   EXPORT DATA
echo   ===========
echo.
echo   1. Export to CSV
echo   2. Export to JSON
echo   3. Export images
echo   4. Back to main menu
echo.
set export_choice=
set /p export_choice="Select an option (1-4): "

if "!export_choice!"=="1" (
    python content_manager\content_manager.py --export csv
) else if "!export_choice!"=="2" (
    python content_manager\content_manager.py --export json
) else if "!export_choice!"=="3" (
    python content_manager\content_manager.py --export-images
)
pause
goto :eof

:UTILITIES
cls
echo.
echo   UTILITIES
echo   =========
echo.
echo   1. Clean database (remove duplicates)
echo   2. Verify data integrity
echo   3. Run tests
echo   4. Back to main menu
echo.
set util_choice=
set /p util_choice="Select an option (1-4): "

if "!util_choice!"=="1" (
    python utils\clean_database.py
) else if "!util_choice!"=="2" (
    python utils\verify_integrity.py
) else if "!util_choice!"=="3" (
    python -m pytest tests/
)
pause
goto :eof

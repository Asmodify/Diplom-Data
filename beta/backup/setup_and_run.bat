@echo off
echo Facebook Scraper with PostgreSQL Setup

REM Check if PostgreSQL is installed
where psql > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PostgreSQL is not installed or not in PATH. Please install PostgreSQL.
    echo Visit https://www.postgresql.org/download/windows/ for installation.
    pause
    exit /b 1
)

echo Setting up PostgreSQL database...
python setup_postgres_db.py

if %ERRORLEVEL% EQU 0 (
    echo PostgreSQL database setup complete!
    echo.
    echo Initializing project...
    python init_project.py
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo Ready to run the Facebook scraper!
        echo.
        
        REM Ask user if they want to run the scraper now
        set /p run_now=Do you want to run the scraper now? (y/n): 
        
        if /i "%run_now%"=="y" (
            echo.
            call run_scraper_all.bat
        ) else (
            echo.
            echo You can run the scraper later with run_scraper_all.bat
        )
    ) else (
        echo Project initialization failed. Please check the logs.
    )
) else (
    echo PostgreSQL database setup failed. Please check the logs.
)

pause

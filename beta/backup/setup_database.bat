@echo off
echo Facebook Scraper with PostgreSQL Setup
echo =======================================

REM Check if PostgreSQL is installed
where psql > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PostgreSQL is not installed or not in PATH.
    echo You can still use pgAdmin if it's installed separately.
)

echo.
echo Database Setup Options:
echo 1. Use pgAdmin (graphical interface)
echo 2. Use SQL script (command line)
echo.
set /p setup_choice=Choose database setup method (1-2): 

if "%setup_choice%"=="1" (
    echo.
    echo =======================================
    echo pgAdmin Setup Instructions:
    echo =======================================
    echo 1. Open pgAdmin and connect to your PostgreSQL server
    echo 2. Right-click on "Databases" and select "Create" ^> "Database..."
    echo 3. Enter "facebook_scraper_beta" as the database name
    echo 4. Set the owner to "postgres" (or your preferred database user)
    echo 5. Click "Save" to create the database
    echo.
    echo After creating the database in pgAdmin, we'll run the table setup script.
    echo.
    set /p continue_setup=Have you created the database in pgAdmin? (y/n): 
    
    if /i "%continue_setup%"=="y" (
        echo.
        echo Creating database tables...
        python setup_postgres_db.py --skip-db-creation
    ) else (
        echo.
        echo Please create the database first, then run this script again.
        echo See PGADMIN_SETUP.md for detailed instructions.
        start notepad.exe PGADMIN_SETUP.md
        pause
        exit /b 1
    )
) else (
    echo.
    echo Using SQL script to create database...
    echo This requires PostgreSQL to be in your PATH and proper credentials.
    psql -U postgres -f create_postgres_db.sql
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create database with SQL script.
        echo Please try the pgAdmin method instead.
        pause
        exit /b 1
    )
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Database setup complete!
    echo.
    echo Initializing project structure...
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
    echo Database setup failed. Please check the logs.
)

pause

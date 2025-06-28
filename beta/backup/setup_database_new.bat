@echo off
title Facebook Scraper - PostgreSQL Database Setup
color 0A
cls
echo ===============================================
echo   Facebook Scraper - PostgreSQL Database Setup
echo ===============================================
echo.

REM Check if PostgreSQL is installed (CLI check)
where psql > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Notice: PostgreSQL command line tools (psql) not found in PATH.
    echo If you're using pgAdmin, this is not a problem.
    echo.
)

echo Please select your preferred database setup method:
echo.
echo [1] Setup with pgAdmin (graphical interface - RECOMMENDED)
echo     - Easier for beginners
echo     - Visual interface
echo     - No command line required
echo.
echo [2] Setup with command line (psql)
echo     - Faster setup for experienced users
echo     - Requires PostgreSQL in PATH
echo.
set /p setup_choice=Your choice (1-2): 

if "%setup_choice%"=="1" (
    cls
    echo ===============================================
    echo   Setting up with pgAdmin
    echo ===============================================
    echo.
    echo Follow these steps to create your database:
    echo.
    echo 1. Open pgAdmin and connect to your PostgreSQL server
    echo 2. Right-click on "Databases" and select "Create" ^> "Database..."
    echo 3. Enter "facebook_scraper_beta" as the database name
    echo 4. Set the owner to "postgres" (or your preferred database user)
    echo 5. Click "Save" to create the database
    echo.
    echo For detailed instructions with screenshots, see PGADMIN_GUIDE.md
    echo.
    set /p open_guide=Would you like to open the detailed guide? (y/n): 
    
    if /i "%open_guide%"=="y" (
        start notepad.exe PGADMIN_GUIDE.md
    )
    
    echo.
    set /p continue_setup=Have you created the database in pgAdmin? (y/n): 
    
    if /i "%continue_setup%"=="y" (
        echo.
        echo Creating database tables...
        python setup_postgres_db.py --skip-db-creation
        
        if %ERRORLEVEL% EQU 0 (
            echo.
            echo Testing database connection...
            python test_postgres_connection.py
        )
    ) else (
        echo.
        echo Please create the database first, then run this script again.
        echo.
        pause
        exit /b 1
    )
) else (
    cls
    echo ===============================================
    echo   Setting up with Command Line (psql)
    echo ===============================================
    echo.
    echo This will create the database using PostgreSQL command line tools.
    echo You will be prompted for the PostgreSQL password if needed.
    echo.
    set /p continue_psql=Continue with command line setup? (y/n): 
    
    if /i "%continue_psql%"=="y" (
        echo.
        echo Creating database with SQL script...
        psql -U postgres -f create_postgres_db.sql
        
        if %ERRORLEVEL% NEQ 0 (
            echo.
            echo Failed to create database with SQL script.
            echo.
            echo Possible reasons:
            echo 1. PostgreSQL is not running
            echo 2. Incorrect password for 'postgres' user
            echo 3. Permission issues
            echo.
            echo Please try the pgAdmin method instead.
            pause
            exit /b 1
        )
    ) else (
        echo Setup cancelled.
        pause
        exit /b 0
    )
)

if %ERRORLEVEL% EQU 0 (
    cls
    echo ===============================================
    echo   Database Setup Complete!
    echo ===============================================
    echo.
    echo Initializing project structure...
    python init_project.py
    
    if %ERRORLEVEL% EQU 0 (
        cls
        echo ===============================================
        echo   Setup Complete - Ready to Use!
        echo ===============================================
        echo.
        echo The Facebook scraper is now ready to use!
        echo.
        echo What would you like to do next?
        echo.
        echo [1] Run the Facebook scraper now
        echo [2] Exit (you can run the scraper later)
        echo.
        set /p next_step=Your choice (1-2): 
        
        if "%next_step%"=="1" (
            echo.
            call run_scraper_all.bat
        ) else (
            echo.
            echo You can run the scraper later with run_scraper_all.bat
            echo.
            echo Thank you for using the Facebook Scraper!
        )
    ) else (
        echo.
        echo Project initialization failed. Please check the logs.
    )
) else (
    echo.
    echo Database setup failed. Please check the logs.
)

pause

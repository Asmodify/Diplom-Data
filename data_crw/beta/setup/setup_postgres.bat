@echo off
echo Creating PostgreSQL database for Facebook scraper...
echo.

set /p postgres_password=Enter your PostgreSQL password for user 'postgres': 
echo.

echo.
echo 1. Creating database...
psql -U postgres -c "CREATE DATABASE facebook_scraper_beta WITH OWNER postgres;" -W
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create database. Please check PostgreSQL installation and try again.
    echo Make sure PostgreSQL is running and the postgres user has the correct password.
    pause
    exit /b 1
)

echo.
echo 2. Running project initialization...
python init_project.py
if %ERRORLEVEL% NEQ 0 (
    echo Project initialization failed. Please check the logs.
    pause
    exit /b 1
) 

echo.
echo 3. Testing database connection...
python test_postgres_connection.py
if %ERRORLEVEL% NEQ 0 (
    echo Database connection test failed. Please review the error message.
    pause
    exit /b 1
)

echo.
echo ✅ PostgreSQL setup completed successfully!
echo.
echo You can now run:
echo   - python manual_login.py    - To log in to Facebook manually
echo   - python facebook_scraper_all.py - To run the full scraper
echo   - python view_comments.py   - To browse and search comments
echo.
pause

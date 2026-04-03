@echo off
echo Testing PostgreSQL Connection for Facebook Scraper
echo ================================================

python test_postgres_connection.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Connection test successful! Your database is properly configured.
) else (
    echo.
    echo Connection test failed. Please review the error message above.
    echo See PGADMIN_GUIDE.md for detailed setup instructions.
    start notepad.exe PGADMIN_GUIDE.md
)

pause

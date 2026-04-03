@echo off
cd /d "%~dp0"
echo Running Facebook Scraper Tests...
echo ==============================

python tests/run_tests.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Some tests failed! See output above for details.
    pause
    exit /b 1
)

echo.
echo All tests passed successfully!
pause

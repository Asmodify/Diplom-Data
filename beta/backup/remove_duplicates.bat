@echo off
cd /d "%~dp0"
title Facebook Scraper - Remove Duplicates
echo ======================================
echo Facebook Scraper - Duplicate Removal
echo ======================================
echo.
echo This tool will remove duplicate:
echo  - Comments
echo  - Post images
echo  - Screenshots
echo.
echo WARNING: This process cannot be undone!
echo.
set /p confirm=Are you sure you want to continue? (y/n): 

if /i "%confirm%" NEQ "y" (
    echo.
    echo Operation cancelled.
    pause
    exit /b
)

echo.
echo Removing duplicates...
python remove_duplicates.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Failed to remove duplicates.
    echo Check the logs for details.
    pause
    exit /b 1
)

echo.
pause

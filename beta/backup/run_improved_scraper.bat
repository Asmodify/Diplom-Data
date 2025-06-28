@echo off
echo ====================================
echo Improved Facebook Scraper With Comments
echo ====================================
echo This script runs the improved Facebook scraper with the fixes for comment extraction.
echo.
echo Options:
echo   - Manual login enabled
echo   - Comment extraction enabled 
echo   - Image downloading enabled
echo   - Screenshots enabled
echo.

python facebook_scraper_all.py --pages-file pages.txt

echo.
echo Scraping completed. Running comment inspection tool to verify results:
python view_comment_data.py

echo.
pause

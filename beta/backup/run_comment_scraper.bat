@echo off
echo ======================================
echo Facebook Comment Scraper
echo ======================================
echo.
echo This will extract comments from posts
echo that were previously scraped.
echo.
echo Press any key to continue...
pause > nul

python scrape_comments.py --max-posts 5

echo.
echo ======================================
echo Press any key to exit
pause > nul

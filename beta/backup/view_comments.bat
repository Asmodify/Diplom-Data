@echo off
cd /d "%~dp0"
title Facebook Comments Viewer
cls

REM ============================================
echo.
echo   FACEBOOK COMMENTS VIEWER
echo   =======================
echo.
echo   This tool allows you to view and search comments
echo   from Facebook posts in the database
echo.
echo   Options:
echo     1. Interactive mode (search and filter)
echo     2. List all posts with comment counts
echo     3. View comments for a specific post ID
echo     q. Quit
echo.
REM ============================================

REM Install dependencies if needed
if not exist ".venv\Scripts\activate.bat" (
    echo Setting up virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

:MENU_LOOP
set choice=
set /p choice="Select an option (1-3, q): "

if "%choice%"=="1" (
    echo.
    echo Starting interactive comments viewer...
    python view_comments.py --interactive
    goto END
)

if "%choice%"=="2" (
    echo.
    echo Listing all posts with comment counts...
    python view_comments.py --list-posts
    goto END
)

if "%choice%"=="3" (
    echo.
    echo Please enter a post ID:
    set /p post_id="Post ID: "
    echo.
    echo Viewing comments for post %post_id%...
    python view_comments.py --post-id %post_id%
    goto END
)

if "%choice%"=="q" (
    echo Exiting...
    exit /b 0
)

echo.
echo Invalid choice, please try again.
goto MENU_LOOP

:END
pause
exit /b %ERRORLEVEL%

pause

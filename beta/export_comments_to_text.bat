@echo off
cd /d "%~dp0"
echo Facebook Comments Text Exporter
echo ===================================

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found! Setting up...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
)

echo.
echo Exporting all Facebook comments to text file...
python export_comments_to_text.py
echo.
echo Done! Text file will be saved in the current directory.
pause

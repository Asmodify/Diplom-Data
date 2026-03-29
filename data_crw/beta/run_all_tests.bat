@echo off
echo ========================================
echo   Running All Tests
echo ========================================
echo.

echo [1/3] Testing ML Analyzer...
python test_ml.py
if errorlevel 1 (
    echo ML Test FAILED
) else (
    echo ML Test PASSED
)
echo.

echo [2/3] Testing Firebase Connection...
python test_firebase.py
if errorlevel 1 (
    echo Firebase Test FAILED - Check credentials
) else (
    echo Firebase Test PASSED
)
echo.

echo [3/3] Testing Google Sheets...
python test_sheets.py
if errorlevel 1 (
    echo Google Sheets Test FAILED - Check credentials
) else (
    echo Google Sheets Test PASSED
)
echo.

echo ========================================
echo   All Tests Complete
echo ========================================
pause

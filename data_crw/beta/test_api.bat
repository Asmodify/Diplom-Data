@echo off
echo ========================================
echo   Testing API Server
echo ========================================
echo Make sure the API server is running first:
echo   python api_server.py
echo.
python test_api.py
echo.
pause

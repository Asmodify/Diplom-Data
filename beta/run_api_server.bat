@echo off
echo ========================================
echo   Starting FastAPI Server
echo ========================================
echo.
echo API will be available at:
echo   http://localhost:8000
echo   http://localhost:8000/docs (Swagger UI)
echo   http://localhost:8000/redoc (ReDoc)
echo.
echo Press Ctrl+C to stop the server
echo.
python api_server.py

@echo off
echo ===================================================
echo Web Scraping Bot - Interview Demo
echo ===================================================
echo.

echo Checking environment...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH. Please install Python 3.9 or higher.
    exit /b 1
)

echo Checking dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies.
    exit /b 1
)

echo.
echo ===================================================
echo Starting Web Scraping Bot Demo
echo ===================================================
echo.

echo Choose a demo option:
echo 1. Full Demo (Scraping, Caching, Reports, Monitoring)
echo 2. Monitoring Only Demo
echo 3. Docker Compose Demo (All Services)
echo.

set /p option="Enter option (1-3): "

if "%option%"=="1" (
    echo Starting Full Demo...
    python demo.py
) else if "%option%"=="2" (
    echo Starting Monitoring Only Demo...
    python demo.py --monitoring-only
) else if "%option%"=="3" (
    echo Starting Docker Compose Demo...
    docker-compose up -d
    echo.
    echo Services started! Access the following URLs:
    echo - Grafana Dashboard: http://localhost:3000 (admin/admin)
    echo - Prometheus: http://localhost:9090
    echo - Web Dashboard: http://localhost:5000
    echo.
    echo Press any key to stop the services...
    pause >nul
    docker-compose down
) else (
    echo Invalid option selected.
    exit /b 1
)

echo.
echo Demo completed.
echo.
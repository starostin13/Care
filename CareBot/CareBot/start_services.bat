@echo off
chcp 65001 >nul
echo Starting CareBot Docker containers...
echo.

echo [1/5] Building containers...
docker-compose build

echo.
echo [2/5] Starting database and redis...
docker-compose up -d database redis

echo.
echo [3/5] Waiting for database to be ready...
timeout /t 10 /nobreak >nul

echo.
echo [4/5] Starting webapp...
docker-compose up -d webapp

echo.
echo [5/5] Starting all services...
docker-compose up -d

echo.
echo Checking container status...
docker-compose ps

echo.
echo Done! Services are starting up.
echo Web interface: http://localhost:8080
echo Mini App: http://localhost:8080/miniapp
echo API Health: http://localhost:8080/health
echo.
pause

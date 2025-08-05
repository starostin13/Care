@echo off
chcp 65001 >nul
cls
echo ========================================
echo    CareBot Docker Management Console
echo ========================================
echo.

:menu
echo [1] Start all services
echo [2] Stop all services  
echo [3] View service status
echo [4] View logs
echo [5] Restart services
echo [6] Build containers
echo [7] Clean up (remove all)
echo [8] Quick health check
echo [0] Exit
echo.
set /p choice="Select option (0-8): "

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto stop_all
if "%choice%"=="3" goto status
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto restart
if "%choice%"=="6" goto build
if "%choice%"=="7" goto cleanup
if "%choice%"=="8" goto healthcheck
if "%choice%"=="0" goto exit
goto menu

:start_all
echo Starting all CareBot services...
docker-compose up -d
echo.
echo Services started. Check status with option 3.
pause
goto menu

:stop_all
echo Stopping all services...
docker-compose down
echo.
echo All services stopped.
pause
goto menu

:status
echo Current service status:
docker-compose ps
echo.
pause
goto menu

:logs
echo.
echo [1] WebApp logs
echo [2] Database logs  
echo [3] Redis logs
echo [4] Nginx logs
echo [5] All logs
echo.
set /p log_choice="Select service (1-5): "

if "%log_choice%"=="1" docker-compose logs webapp --tail 20
if "%log_choice%"=="2" docker-compose logs database --tail 20
if "%log_choice%"=="3" docker-compose logs redis --tail 20
if "%log_choice%"=="4" docker-compose logs nginx --tail 20
if "%log_choice%"=="5" docker-compose logs --tail 10
echo.
pause
goto menu

:restart
echo Restarting all services...
docker-compose restart
echo.
echo Services restarted.
pause
goto menu

:build
echo Building all containers...
docker-compose build
echo.
echo Build complete.
pause
goto menu

:cleanup
echo WARNING: This will remove all containers, images, and data!
set /p confirm="Are you sure? (y/N): "
if /i "%confirm%"=="y" (
    docker-compose down -v --rmi all
    echo Cleanup complete.
) else (
    echo Cleanup cancelled.
)
pause
goto menu

:healthcheck
echo Checking service health...
echo.
echo WebApp health:
curl -s http://localhost:8080/health 2>nul || echo Could not connect to WebApp
echo.
echo Nginx status:
curl -s -o nul -w "HTTP Status: %%{http_code}" http://localhost 2>nul || echo Could not connect to Nginx
echo.
echo.
echo Direct service status:
docker-compose ps --format "{{.Name}}: {{.Status}}"
echo.
pause
goto menu

:exit
echo Goodbye!
exit /b 0

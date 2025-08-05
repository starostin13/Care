@echo off
chcp 65001 >nul 2>&1
REM Скрипт для просмотра логов и диагностики CareBot

echo CareBot Logs and Diagnostics
echo =============================

:menu
echo.
echo Выберите действие:
echo 1. Показать статус всех контейнеров
echo 2. Показать логи всех сервисов
echo 3. Показать логи веб-приложения
echo 4. Показать логи Telegram бота
echo 5. Показать логи базы данных
echo 6. Проверить health check
echo 7. Перезапустить все сервисы
echo 8. Остановить все сервисы
echo 9. Выход
echo.

set /p choice="Введите номер (1-9): "

if "%choice%"=="1" goto status
if "%choice%"=="2" goto logs_all
if "%choice%"=="3" goto logs_webapp
if "%choice%"=="4" goto logs_bot
if "%choice%"=="5" goto logs_db
if "%choice%"=="6" goto health
if "%choice%"=="7" goto restart
if "%choice%"=="8" goto stop
if "%choice%"=="9" goto exit
goto menu

:status
echo [INFO] Статус контейнеров:
docker-compose ps
goto menu

:logs_all
echo [INFO] Логи всех сервисов (Ctrl+C для остановки):
docker-compose logs -f
goto menu

:logs_webapp
echo [INFO] Логи веб-приложения (Ctrl+C для остановки):
docker-compose logs -f webapp
goto menu

:logs_bot
echo [INFO] Логи Telegram бота (Ctrl+C для остановки):
docker-compose logs -f telegram_bot
goto menu

:logs_db
echo [INFO] Логи базы данных (Ctrl+C для остановки):
docker-compose logs -f database
goto menu

:health
echo [INFO] Проверка health check:
echo Попытка подключения к http://localhost/health...
curl -f http://localhost/health
if errorlevel 1 (
    echo [ERROR] Health check не прошел. Возможные причины:
    echo   - Сервисы еще не запустились полностью
    echo   - Ошибка в конфигурации
    echo   - Проблемы с сетью
    echo   Проверьте логи: docker-compose logs webapp
) else (
    echo [SUCCESS] Health check прошел успешно!
)
goto menu

:restart
echo [INFO] Перезапуск всех сервисов...
docker-compose restart
echo [SUCCESS] Перезапуск завершен
goto menu

:stop
echo [INFO] Остановка всех сервисов...
docker-compose down
echo [SUCCESS] Все сервисы остановлены
goto menu

:exit
echo [INFO] Выход...
exit /b 0

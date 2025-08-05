@echo off
chcp 65001 >nul 2>&1
REM Скрипт для развертывания CareBot в Docker на Windows (без эмодзи)

echo CareBot Docker Deployment Script for Windows
echo ================================================

REM Проверка наличия Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker не установлен. Установите Docker Desktop и попробуйте снова.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose не установлен. Обновите Docker Desktop.
    pause
    exit /b 1
)

REM Создание .env файла если его нет
if not exist .env (
    echo [INFO] Создание .env файла...
    copy .env.example .env >nul
    echo [WARNING] ВНИМАНИЕ: Отредактируйте .env файл перед продолжением!
    echo    Особенно важно установить:
    echo    - TELEGRAM_BOT_TOKEN
    echo    - DB_PASSWORD  
    echo    - SECRET_KEY
    echo.
    echo [INFO] Нажмите любую клавишу после редактирования .env файла...
    pause >nul
)

REM Создание необходимых директорий
echo [INFO] Создание директорий...
if not exist logs mkdir logs >nul 2>&1
if not exist db\data mkdir db\data >nul 2>&1
if not exist static\uploads mkdir static\uploads >nul 2>&1

REM Остановка существующих контейнеров
echo [INFO] Остановка существующих контейнеров...
docker-compose down --remove-orphans >nul 2>&1

REM Сборка образов
echo [INFO] Сборка Docker образов (это может занять несколько минут)...
docker-compose build --no-cache

REM Запуск сервисов
echo [INFO] Запуск сервисов...
docker-compose up -d

REM Ожидание готовности сервисов
echo [INFO] Ожидание готовности сервисов (30 секунд)...
timeout /t 30 /nobreak >nul

REM Проверка статуса
echo [INFO] Проверка статуса сервисов...
docker-compose ps

REM Проверка health check
echo [INFO] Проверка health check...
curl -f http://localhost/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Веб-приложение еще не готово. Проверьте логи командой:
    echo           docker-compose logs webapp
) else (
    echo [SUCCESS] Веб-приложение готово!
)

echo.
echo ================================================
echo [SUCCESS] Развертывание завершено!
echo ================================================
echo.
echo Доступные сервисы:
echo   Mini App:        http://localhost/miniapp
echo   Карта:           http://localhost/map  
echo   Станция печати:  http://localhost/print-station
echo   API:             http://localhost/api/
echo   Health Check:    http://localhost/health
echo.
echo Полезные команды:
echo   docker-compose logs -f              # Просмотр логов
echo   docker-compose restart telegram_bot # Перезапуск бота
echo   docker-compose down                 # Остановка всех сервисов
echo.
echo Настройка Telegram Bot:
echo   1. Создайте бота через @BotFather
echo   2. Получите токен и добавьте его в .env
echo   3. Настройте Mini App URL: http://your-domain/miniapp
echo.

REM Показ логов в реальном времени (опционально)
set /p choice="Показать логи в реальном времени? (y/N): "
if /i "%choice%"=="y" (
    echo [INFO] Показ логов в реальном времени (Ctrl+C для выхода)...
    docker-compose logs -f
) else (
    echo [INFO] Для просмотра логов используйте: docker-compose logs -f
    echo [INFO] Нажмите любую клавишу для выхода...
    pause >nul
)

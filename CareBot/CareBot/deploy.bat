@echo off
REM Скрипт для развертывания CareBot в Docker на Windows

echo 🐳 CareBot Docker Deployment Script for Windows
echo ================================================

REM Проверка наличия Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker не установлен. Установите Docker Desktop и попробуйте снова.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose не установлен. Обновите Docker Desktop.
    pause
    exit /b 1
)

REM Создание .env файла если его нет
if not exist .env (
    echo 📝 Создание .env файла...
    copy .env.example .env
    echo ⚠️  ВНИМАНИЕ: Отредактируйте .env файл перед продолжением!
    echo    Особенно важно установить:
    echo    - TELEGRAM_BOT_TOKEN
    echo    - DB_PASSWORD  
    echo    - SECRET_KEY
    echo.
    pause
)

REM Создание необходимых директорий
echo 📁 Создание директорий...
if not exist logs mkdir logs
if not exist db\data mkdir db\data
if not exist static\uploads mkdir static\uploads

REM Остановка существующих контейнеров
echo 🛑 Остановка существующих контейнеров...
docker-compose down --remove-orphans

REM Сборка образов
echo 🏗️  Сборка Docker образов...
docker-compose build --no-cache

REM Запуск сервисов
echo 🚀 Запуск сервисов...
docker-compose up -d

REM Ожидание готовности сервисов
echo ⏳ Ожидание готовности сервисов...
timeout /t 30 /nobreak >nul

REM Проверка статуса
echo 🔍 Проверка статуса сервисов...
docker-compose ps

REM Проверка health check
echo 🏥 Проверка здоровья приложения...
curl -f http://localhost/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Веб-приложение еще не готово, проверьте логи
) else (
    echo ✅ Веб-приложение готово!
)

echo.
echo 🎉 Развертывание завершено!
echo ==========================
echo 📱 Mini App: http://localhost/miniapp
echo 🗺️  Карта: http://localhost/map  
echo 🖨️  Станция печати: http://localhost/print-station
echo 🔧 API: http://localhost/api/
echo 💊 Health Check: http://localhost/health
echo.
echo 📋 Полезные команды:
echo   docker-compose logs -f              # Просмотр логов
echo   docker-compose restart telegram_bot # Перезапуск бота
echo   docker-compose down                 # Остановка всех сервисов
echo.
echo 🤖 Не забудьте настроить Telegram Bot:
echo   1. Создайте бота через @BotFather
echo   2. Получите токен и добавьте его в .env
echo   3. Настройте Mini App URL: http://your-domain/miniapp
echo.

REM Показ логов в реальном времени (опционально)
set /p choice="Показать логи в реальном времени? (y/N): "
if /i "%choice%"=="y" (
    docker-compose logs -f
) else (
    echo Для просмотра логов используйте: docker-compose logs -f
    pause
)

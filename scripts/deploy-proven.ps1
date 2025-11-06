# Быстрое развертывание CareBot - Проверенный метод
# НЕ ИЗМЕНЯТЬ! Это работающая конфигурация

param(
    [string]$Action = "deploy"
)

$SERVER = "192.168.0.125"
$USER = "ubuntu"
$REMOTE_PATH = "/home/ubuntu/carebot"

function Write-Status {
    param([string]$Message)
    Write-Host "🔧 $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

switch ($Action) {
    "deploy" {
        Write-Status "Начинаем развертывание CareBot (проверенный метод)..."
        
        # 1. Копирование файлов
        Write-Status "Копируем файлы на сервер..."
        scp -r CareBot ${USER}@${SERVER}:${REMOTE_PATH}/
        scp Dockerfile.carebot ${USER}@${SERVER}:${REMOTE_PATH}/
        scp Dockerfile.sqlite-web ${USER}@${SERVER}:${REMOTE_PATH}/
        scp sqlite_web_interface.py ${USER}@${SERVER}:${REMOTE_PATH}/
        scp docker-compose.simple.yml ${USER}@${SERVER}:${REMOTE_PATH}/
        
        # 2. Подготовка на сервере
        Write-Status "Подготавливаем конфигурацию на сервере..."
        ssh ${USER}@${SERVER} "cd ${REMOTE_PATH} && mv docker-compose.simple.yml docker-compose.yml"
        
        # 3. Остановка старых контейнеров
        Write-Status "Останавливаем старые контейнеры..."
        ssh ${USER}@${SERVER} "cd ${REMOTE_PATH} && docker-compose down"
        
        # 4. Сборка образов
        Write-Status "Собираем новые образы..."
        ssh ${USER}@${SERVER} "cd ${REMOTE_PATH} && docker-compose build --no-cache"
        
        # 5. Запуск контейнеров
        Write-Status "Запускаем контейнеры..."
        ssh ${USER}@${SERVER} "cd ${REMOTE_PATH} && docker-compose up -d"
        
        # 6. Проверка статуса
        Write-Status "Проверяем статус контейнеров..."
        ssh ${USER}@${SERVER} "cd ${REMOTE_PATH} && docker-compose ps"
        
        # 7. Проверка здоровья
        Write-Status "Ожидаем запуска сервисов..."
        Start-Sleep -Seconds 10
        
        try {
            $healthResponse = Invoke-WebRequest -Uri "http://${SERVER}:5555/health" -UseBasicParsing -TimeoutSec 10
            if ($healthResponse.StatusCode -eq 200) {
                Write-Success "CareBot работает! Health check: OK"
            }
        }
        catch {
            Write-Error "CareBot health check не прошел: $($_.Exception.Message)"
        }
        
        try {
            $webResponse = Invoke-WebRequest -Uri "http://${SERVER}:8080" -UseBasicParsing -TimeoutSec 10
            if ($webResponse.StatusCode -eq 200) {
                Write-Success "SQLite Web работает! Доступен на http://${SERVER}:8080"
            }
        }
        catch {
            Write-Error "SQLite Web недоступен: $($_.Exception.Message)"
        }
        
        Write-Success "Развертывание завершено!"
        Write-Host "📊 CareBot API: http://${SERVER}:5555" -ForegroundColor Yellow
        Write-Host "🗄️  SQLite Web: http://${SERVER}:8080" -ForegroundColor Yellow
    }
    
    "status" {
        Write-Status "Проверяем статус сервисов..."
        ssh ${USER}@${SERVER} "cd ${REMOTE_PATH} && docker-compose ps"
        
        try {
            Invoke-WebRequest -Uri "http://${SERVER}:5555/health" -UseBasicParsing | Out-Null
            Write-Success "CareBot: РАБОТАЕТ"
        }
        catch {
            Write-Error "CareBot: НЕ ДОСТУПЕН"
        }
        
        try {
            Invoke-WebRequest -Uri "http://${SERVER}:8080" -UseBasicParsing | Out-Null
            Write-Success "SQLite Web: РАБОТАЕТ"
        }
        catch {
            Write-Error "SQLite Web: НЕ ДОСТУПЕН"
        }
    }
    
    "logs" {
        Write-Status "Показываем логи CareBot..."
        ssh ${USER}@${SERVER} "cd ${REMOTE_PATH} && docker-compose logs carebot"
    }
    
    "restart" {
        Write-Status "Перезапускаем сервисы..."
        ssh ${USER}@${SERVER} "cd ${REMOTE_PATH} && docker-compose restart"
        Write-Success "Сервисы перезапущены"
    }
    
    "stop" {
        Write-Status "Останавливаем сервисы..."
        ssh ${USER}@${SERVER} "cd ${REMOTE_PATH} && docker-compose down"
        Write-Success "Сервисы остановлены"
    }
    
    default {
        Write-Host "Использование: .\deploy-proven.ps1 [deploy|status|logs|restart|stop]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Команды:" -ForegroundColor Cyan
        Write-Host "  deploy  - Полное развертывание (по умолчанию)" -ForegroundColor White
        Write-Host "  status  - Проверка статуса сервисов" -ForegroundColor White
        Write-Host "  logs    - Просмотр логов CareBot" -ForegroundColor White
        Write-Host "  restart - Перезапуск сервисов" -ForegroundColor White
        Write-Host "  stop    - Остановка сервисов" -ForegroundColor White
    }
}
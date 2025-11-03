# Quick Production Update Script
# Быстрое обновление без проверок - для экстренных случаев

param(
    [string]$File,
    [switch]$All
)

$SERVER_HOST = "ubuntu@192.168.1.125"
$PRODUCTION_PATH = "/home/ubuntu/carebot-production"

function Write-Info($text) {
    Write-Host "ℹ️  $text" -ForegroundColor Cyan
}

function Write-Success($text) {
    Write-Host "✅ $text" -ForegroundColor Green
}

function Write-Error($text) {
    Write-Host "❌ $text" -ForegroundColor Red
}

if ($All) {
    Write-Info "Быстрое полное обновление..."
    
    # Копируем все измененные файлы
    Write-Info "Синхронизируем все файлы..."
    rsync -avz --exclude='.git' --exclude='*.log' --exclude='__pycache__' ./ "${SERVER_HOST}:${PRODUCTION_PATH}/"
    
    # Перезапускаем без пересборки
    Write-Info "Перезапускаем сервис..."
    ssh $SERVER_HOST "cd $PRODUCTION_PATH && docker-compose -f docker-compose.production.yml restart"
    
    Write-Success "Быстрое обновление завершено!"
    
} elseif ($File) {
    Write-Info "Обновляем файл: $File"
    
    if (-not (Test-Path $File)) {
        Write-Error "Файл $File не найден!"
        exit 1
    }
    
    # Копируем один файл
    $remoteDir = Split-Path $File -Parent
    if ($remoteDir) {
        ssh $SERVER_HOST "mkdir -p $PRODUCTION_PATH/$remoteDir"
    }
    
    scp $File "${SERVER_HOST}:${PRODUCTION_PATH}/$File"
    
    # Перезапускаем только если это Python файл
    if ($File -match "\.py$") {
        Write-Info "Перезапускаем Python сервис..."
        ssh $SERVER_HOST "cd $PRODUCTION_PATH && docker-compose -f docker-compose.production.yml restart"
    }
    
    Write-Success "Файл $File обновлен!"
    
} else {
    Write-Host ""
    Write-Host "🚀 Quick Production Update" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Использование:"
    Write-Host "  .\scripts\quick-update.ps1 -File <путь к файлу>"
    Write-Host "  .\scripts\quick-update.ps1 -All"
    Write-Host ""
    Write-Host "Примеры:"
    Write-Host "  .\scripts\quick-update.ps1 -File CareBot/CareBot/handlers.py"
    Write-Host "  .\scripts\quick-update.ps1 -All"
    Write-Host ""
}
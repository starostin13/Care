# Скрипт автоматического бэкапа базы данных CareBot (PowerShell версия)
# Для запуска с Windows машины

param(
    [string]$Server = "192.168.0.125",
    [string]$User = "ubuntu",
    [string]$RemotePath = "/home/ubuntu/carebot"
)

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

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

Write-Status "Начинаем создание бэкапа базы данных CareBot..."
Write-Host "📅 Время: $(Get-Date)" -ForegroundColor White
Write-Host "🖥️  Сервер: $Server" -ForegroundColor White

# Генерация временной метки
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFilename = "carebot_backup_$timestamp.sql"

Write-Status "Создаем бэкап на удаленном сервере..."

# Выполнение скрипта бэкапа на сервере
$sshCommand = "cd $RemotePath && ./scripts/backup-database.sh"
$result = ssh ${User}@${Server} $sshCommand

if ($LASTEXITCODE -eq 0) {
    Write-Success "Бэкап создан успешно на сервере!"
    Write-Host "📁 Файл: $backupFilename" -ForegroundColor Yellow
    
    # Получение информации о последнем бэкапе
    $backupInfo = ssh ${User}@${Server} "ls -la $RemotePath/backups/latest_backup.*"
    Write-Host "📊 Информация о бэкапе:" -ForegroundColor Cyan
    Write-Host $backupInfo -ForegroundColor White
} else {
    Write-Error "Ошибка создания бэкапа!"
    Write-Host $result -ForegroundColor Red
    exit 1
}

# Опционально: скачивание бэкапа на локальную машину
$downloadChoice = Read-Host "Скачать бэкап на локальную машину? (y/n)"
if ($downloadChoice -eq 'y' -or $downloadChoice -eq 'Y') {
    $localBackupDir = ".\backups"
    if (-not (Test-Path $localBackupDir)) {
        New-Item -ItemType Directory -Path $localBackupDir | Out-Null
    }
    
    Write-Status "Скачиваем бэкап..."
    scp ${User}@${Server}:${RemotePath}/backups/latest_backup.sql "$localBackupDir\$backupFilename"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Бэкап скачан: $localBackupDir\$backupFilename"
    } else {
        Write-Error "Ошибка скачивания бэкапа"
    }
}

Write-Success "Операция бэкапа завершена!"
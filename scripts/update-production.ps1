# CareBot Production Update Script (LEGACY - prefer scripts/wsl2-deploy.ps1)
param(
    [string]$Action = "update",
    [switch]$Force,
    [switch]$SkipHealthCheck
)

# Configuration
$SERVER_HOST = "ubuntu@192.168.1.125"
$PRODUCTION_PATH = "/home/ubuntu/carebot-production"
$LOCAL_ENV_FILE = ".env"
$HEALTH_URL = "http://192.168.1.125:5555/health"

# Helper functions
function Write-Success($text) { Write-Host "SUCCESS: $text" -ForegroundColor Green }
function Write-Error($text) { Write-Host "ERROR: $text" -ForegroundColor Red }
function Write-Info($text) { Write-Host "INFO: $text" -ForegroundColor Cyan }
function Write-Warning($text) { Write-Host "WARNING: $text" -ForegroundColor Yellow }

# Get latest image SHA
function Get-LatestImageSHA {
    Write-Info "Getting latest built image SHA..."
    $imageSHA = ssh $SERVER_HOST "cd $PRODUCTION_PATH; docker images --format '{{.ID}}' --filter 'reference=carebot:latest' | head -1 | cut -d':' -f2 | cut -c1-12"
    
    if ($LASTEXITCODE -eq 0 -and $imageSHA) {
        Write-Success "Latest image SHA: $imageSHA"
        return $imageSHA
    }
    return $null
}

# Build image on production host
function Build-ProductionImage {
    Write-Info "Building production image on server..."
    ssh $SERVER_HOST "cd $PRODUCTION_PATH; docker build -t carebot:latest -f Dockerfile ."

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Server-side Docker build failed"
        return $false
    }

    Write-Success "Production image built successfully"
    return $true
}

# Safely stop and remove old container
function Stop-OldContainer {
    Write-Info "Safely stopping old container..."
    
    # Check if container exists
    $containerExists = ssh $SERVER_HOST "docker ps -a --filter 'name=carebot_production' --format '{{.Names}}' | grep -c carebot_production 2>/dev/null || echo '0'"
    
    if ($containerExists -eq "0" -or $null -eq $containerExists) {
        Write-Info "No old container found, skipping stop"
        return $true
    }
    
    # Check container status
    $status = ssh $SERVER_HOST "docker ps --all --filter 'name=carebot_production' --format '{{.State}}' 2>/dev/null || echo 'not-found'"
    
    if ($status -eq "running") {
        Write-Info "Container is running, stopping..."
        ssh $SERVER_HOST "docker stop carebot_production --time=30 2>&1"
        Start-Sleep -Seconds 2
    }
    
    # Remove the container
    Write-Info "Removing old container..."
    ssh $SERVER_HOST "docker rm carebot_production 2>&1"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Failed to remove container (may not exist), continuing..."
    }
    
    Write-Success "Old container cleaned up"
    return $true
}

# Production safety check
function Test-ProductionSafety {
    Write-Info "Running production safety check..."
    
    try {
        python scripts\check-production-safety.py
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Success "Production safety check passed"
            return $true
        } else {
            Write-Error "Production safety check FAILED!"
            Write-Warning "Fix security issues before deploying to production"
            return $false
        }
    } catch {
        Write-Error "Failed to run safety check: $($_.Exception.Message)"
        return $false
    }
}

# Get telegram token from .env
function Get-TelegramToken {
    if (-not (Test-Path $LOCAL_ENV_FILE)) {
        Write-Error "File $LOCAL_ENV_FILE not found!"
        return $null
    }
    
    $token = Get-Content $LOCAL_ENV_FILE | Where-Object { $_ -match "TELEGRAM_BOT_TOKEN=" } | ForEach-Object { $_.Split('=')[1] }
    return $token
}

# Get telegram token
function Test-Token {
    Write-Info "Checking Telegram token..."
    
    if (-not (Test-Path $LOCAL_ENV_FILE)) {
        Write-Error "File $LOCAL_ENV_FILE not found!"
        return $false
    }
    
    $token = Get-TelegramToken
    
    if (-not $token) {
        Write-Error "Token not found in $LOCAL_ENV_FILE"
        return $false
    }
    
    Write-Success "Token found: $($token.Substring(0,10))..."
    return $true
}

# Sync files to server
function Sync-Files {
    Write-Info "Syncing files to server..."
    
    $filesToSync = @(
        "CareBot/CareBot/handlers.py",
        "CareBot/CareBot/views.py",
        "CareBot/CareBot/map_export_service.py",
        "CareBot/CareBot/warmaster_helper.py", 
        "CareBot/CareBot/settings_helper.py",
        "CareBot/CareBot/schedule_helper.py",
        "CareBot/CareBot/mission_helper.py",
        "CareBot/CareBot/features.py",
        "CareBot/CareBot/register_features.py",
        "CareBot/CareBot/common_resource_feature.py",
        "CareBot/CareBot/players_helper.py",
        "CareBot/CareBot/map_helper.py",
        "CareBot/CareBot/map_exporter.py",
        "CareBot/CareBot/sqllite_helper.py",
        "CareBot/CareBot/models.py",
        "CareBot/CareBot/mission_message_builder.py",
        "CareBot/CareBot/feature_flags_helper.py",
        "CareBot/CareBot/keyboard_constructor.py",
        "CareBot/CareBot/localization.py",
        "CareBot/CareBot/notification_service.py",
        "CareBot/CareBot/migrate_db.py",
        "CareBot/CareBot/config.py",
        "CareBot/CareBot/templates/battles.html",
        "CareBot/run_hybrid.py",
        "CareBot/requirements.txt",
        "Dockerfile",
        "entrypoint.sh",
        "docker-compose.production.yml"
    )
    
    # Синхронизируем основные файлы
    foreach ($file in $filesToSync) {
        if (Test-Path $file) {
            Write-Host "  Copying $file..."
            
            $remoteDir = Split-Path $file -Parent
            if ($remoteDir) {
                ssh $SERVER_HOST "mkdir -p $PRODUCTION_PATH/$remoteDir"
            }
            
            scp $file "${SERVER_HOST}:${PRODUCTION_PATH}/$file"
        } else {
            Write-Warning "File $file not found, skipping"
        }
    }
    
    # Синхронизируем миграции в отдельную папку
    Write-Info "Syncing migrations to separate directory..."
    ssh $SERVER_HOST "mkdir -p $PRODUCTION_PATH/migrations"
    
    $migrationFiles = Get-ChildItem -Path "CareBot/CareBot/migrations/" -File -ErrorAction SilentlyContinue
    foreach ($migration in $migrationFiles) {
        Write-Host "  Copying migration: $($migration.Name)..."
        scp "CareBot/CareBot/migrations/$($migration.Name)" "${SERVER_HOST}:${PRODUCTION_PATH}/migrations/$($migration.Name)"
    }

    # Синхронизируем assets для деплоев WH40K
    Write-Info "Syncing WH40K deploy assets..."
    ssh $SERVER_HOST "mkdir -p $PRODUCTION_PATH/CareBot/CareBot/assets/deploys"

    $deployAssetFiles = Get-ChildItem -Path "CareBot/CareBot/assets/deploys" -File -ErrorAction SilentlyContinue
    foreach ($asset in $deployAssetFiles) {
        Write-Host "  Copying deploy asset: $($asset.Name)..."
        scp "CareBot/CareBot/assets/deploys/$($asset.Name)" "${SERVER_HOST}:${PRODUCTION_PATH}/CareBot/CareBot/assets/deploys/$($asset.Name)"
    }
    
    Write-Success "File sync completed"
    return $true
}

# Test health check
function Test-Health {
    Write-Info "Checking service health..."
    
    Start-Sleep -Seconds 10
    
    try {
        $response = Invoke-WebRequest -Uri $HEALTH_URL -Method GET -TimeoutSec 10 -Proxy $null
        
        if ($response.StatusCode -eq 200) {
            $healthData = $response.Content | ConvertFrom-Json
            Write-Success "Service is healthy! Status: $($healthData.status)"
            return $true
        }
    }
    catch {
        Write-Warning "Health check failed: $($_.Exception.Message)"
        return $false
    }
    
    return $false
}

# Update production with safe container handling
function Update-Production {
    Write-Host "Starting CareBot Production Update (LEGACY)" -ForegroundColor Yellow
    Write-Warning "This legacy flow builds on the server. Prefer scripts/wsl2-deploy.ps1 for WSL2 builds."
    
    # КРИТИЧЕСКАЯ проверка безопасности перед деплоем
    if (-not (Test-ProductionSafety)) {
        Write-Error "Production safety check FAILED! Deployment BLOCKED."
        Write-Warning "Fix all security issues before deploying to production."
        return $false
    }
    
    if (-not (Test-Token)) { return $false }
    
    $token = Get-TelegramToken
    if (-not $token) {
        Write-Error "Failed to get Telegram token"
        return $false
    }
    
    # Create backup before update
    if (-not $Force) {
        $answer = Read-Host "Create backup before update? (Y/n)"
        if ($answer -ne "n" -and $answer -ne "N") {
            Create-Backup
        }
    } else {
        Create-Backup
    }
    
    if (-not (Sync-Files)) { return $false }

    if (-not (Build-ProductionImage)) { return $false }
    
    # Get the new image SHA
    $imageSHA = Get-LatestImageSHA
    if (-not $imageSHA) {
        Write-Error "Failed to get built image SHA"
        return $false
    }
    
    # Safely stop and remove old container
    if (-not (Stop-OldContainer)) {
        Write-Error "Failed to stop old container"
        return $false
    }
    
    Write-Info "Starting new container with image: $imageSHA..."
    
    # Create new container using docker run (bypasses docker-compose metadata issues)
    ssh $SERVER_HOST "docker run -d --name carebot_production -p 5555:5555 -v carebot_data:/app/data -v ${PRODUCTION_PATH}/migrations:/app/CareBot/migrations -e SERVER_HOST=0.0.0.0 -e SERVER_PORT=5555 -e DATABASE_PATH=/app/data/game_database.db -e TELEGRAM_BOT_TOKEN='${token}' --restart unless-stopped --network carebot-network carebot:latest 2>&1"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start new container"
        return $false
    }
    
    Write-Success "New container started!"
    
    if (-not $SkipHealthCheck) {
        Test-Health
    }
    
    Write-Success "Update completed!"
    return $true
}

# Start admin mode with sqlite-web
function Start-AdminMode {
    Write-Info "Starting admin mode with SQLite web interface..."
    
    ssh $SERVER_HOST "cd $PRODUCTION_PATH; docker compose -f docker-compose.production.yml --profile admin up -d"
    
    Start-Sleep -Seconds 5
    
    Write-Success "Admin mode started!"
    Write-Info "SQLite web interface: http://192.168.1.125:8080"
    Write-Info "CareBot health: $HEALTH_URL"
}

# Stop admin mode
function Stop-AdminMode {
    Write-Info "Stopping admin mode..."
    
    ssh $SERVER_HOST "cd $PRODUCTION_PATH; docker compose -f docker-compose.production.yml --profile admin down"
    
    Write-Success "Admin mode stopped!"
}

# Start/Stop/Restart services
function Start-Service {
    ssh $SERVER_HOST "cd $PRODUCTION_PATH; docker compose -f docker-compose.production.yml up -d"
    Write-Success "Service started"
}

function Stop-Service {
    ssh $SERVER_HOST "cd $PRODUCTION_PATH; docker compose -f docker-compose.production.yml down"
    Write-Success "Service stopped"
}

function Restart-Service {
    Write-Info "Rebuilding image and restarting service..."
    if (-not (Build-ProductionImage)) { return }
    
    # Get the new image SHA
    $imageSHA = Get-LatestImageSHA
    if (-not $imageSHA) {
        Write-Error "Failed to get built image SHA"
        return $false
    }
    
    # Get token
    $token = Get-TelegramToken
    if (-not $token) {
        Write-Error "Failed to get Telegram token"
        return $false
    }
    
    # Safely stop and remove old container
    if (-not (Stop-OldContainer)) {
        Write-Warning "Failed to stop old container, continuing..."
    }
    
    # Start new container
    Write-Info "Starting container with rebuilt image: $imageSHA..."
    ssh $SERVER_HOST "docker run -d --name carebot_production -p 5555:5555 -v carebot_data:/app/data -v ${PRODUCTION_PATH}/migrations:/app/CareBot/migrations -e SERVER_HOST=0.0.0.0 -e SERVER_PORT=5555 -e DATABASE_PATH=/app/data/game_database.db -e TELEGRAM_BOT_TOKEN='${token}' --restart unless-stopped --network carebot-network carebot:latest 2>&1"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Service restarted successfully"
    } else {
        Write-Error "Failed to restart service"
        return $false
    }
}

# Sync only migrations
function Sync-Migrations {
    Write-Info "Syncing only migration files..."
    
    # Создаем папку для миграций
    ssh $SERVER_HOST "mkdir -p $PRODUCTION_PATH/migrations"
    
    $migrationFiles = Get-ChildItem -Path "CareBot/CareBot/migrations/" -File -ErrorAction SilentlyContinue
    $migrationCount = 0
    
    foreach ($migration in $migrationFiles) {
        Write-Host "  Copying migration: $($migration.Name)..."
        scp "CareBot/CareBot/migrations/$($migration.Name)" "${SERVER_HOST}:${PRODUCTION_PATH}/migrations/$($migration.Name)"
        $migrationCount++
    }
    
    Write-Success "Synced $migrationCount migration files"
    return $true
}

# Apply migrations manually
function Apply-Migrations {
    Write-Info "Applying migrations in production..."
    
    ssh $SERVER_HOST "docker exec carebot_production python /app/CareBot/CareBot/migrate_db.py"
    
    Write-Success "Migrations applied"
}

# Check migration status
function Check-MigrationStatus {
    Write-Info "Checking migration status..."
    
    ssh $SERVER_HOST "docker exec carebot_production python /app/CareBot/CareBot/migrate_db.py --status"
}

# Create backup
function Create-Backup {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = "carebot-backup-$timestamp"
    
    Write-Info "Creating backup..."
    ssh $SERVER_HOST "cd /home/ubuntu; cp -r carebot-production $backupPath"
    
    Write-Success "Backup created: $backupPath"
}

# Main script logic
switch ($Action.ToLower()) {
    "update" {
        Update-Production
    }
    "status" {
        Test-Health
    }
    "logs" {
        ssh $SERVER_HOST "cd $PRODUCTION_PATH; docker compose -f docker-compose.production.yml logs --tail=20"
    }
    "admin" {
        Start-AdminMode
    }
    "stop-admin" {
        Stop-AdminMode
    }
    "start" {
        Start-Service
    }
    "stop" {
        Stop-Service
    }
    "restart" {
        Restart-Service
    }
    "migrations" {
        Sync-Migrations
    }
    "apply-migrations" {
        Apply-Migrations
    }
    "migration-status" {
        Check-MigrationStatus
    }
    "build" {
        Build-ProductionImage
    }
    "backup" {
        Create-Backup
    }
    "safety-check" {
        Test-ProductionSafety | Out-Null
    }
    default {
        Write-Host ""
        Write-Host "CareBot Production Update Script" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Usage: .\scripts\update-production.ps1 [action]"
        Write-Host ""
        Write-Host "Actions:"
        Write-Host "  update           - Update production (default)"
        Write-Host "  status           - Check health"
        Write-Host "  logs             - Show logs"
        Write-Host "  admin            - Start admin mode with SQLite web interface"
        Write-Host "  stop-admin       - Stop admin mode"
        Write-Host "  start            - Start services"
        Write-Host "  stop             - Stop services"
        Write-Host "  restart          - Restart services"
        Write-Host "  backup           - Create backup"
        Write-Host "  migrations       - Sync only migration files"
        Write-Host "  apply-migrations - Apply migrations manually"
        Write-Host "  migration-status - Check migration status"
        Write-Host "  build            - Build production image on server"
        Write-Host "  safety-check     - Run production safety validation"
        Write-Host ""
        Write-Host "Options:"
        Write-Host "  -Force           - Skip confirmations"
        Write-Host "  -SkipHealthCheck - Skip health check"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  .\scripts\update-production.ps1 admin"
        Write-Host "  .\scripts\update-production.ps1 migrations"
        Write-Host "  .\scripts\update-production.ps1 update -Force"
    }
}
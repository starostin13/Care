# CareBot Deploy Script - Protected Working Configuration
# DO NOT CHANGE! This is a tested and working configuration

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

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

switch ($Action) {
    "deploy" {
        Write-Status "Starting CareBot deployment (proven method)..."
        
        # 0. Create database backup BEFORE deployment
        Write-Status "Creating database backup before deployment..."
        try {
            $backupCommand = "cd ${REMOTE_PATH}; ./scripts/backup-database.sh 2>/dev/null"
            ssh ${USER}@${SERVER} $backupCommand | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Backup created successfully before deployment"
            } else {
                Write-Warning "Could not create backup (possibly first deployment)"
            }
        }
        catch {
            Write-Warning "Warning: Backup not created - $($_.Exception.Message)"
        }
        
        # 1. Copy files
        Write-Status "Copying files to server..."
        scp -r CareBot ${USER}@${SERVER}:${REMOTE_PATH}/
        scp Dockerfile.carebot ${USER}@${SERVER}:${REMOTE_PATH}/
        scp Dockerfile.sqlite-web ${USER}@${SERVER}:${REMOTE_PATH}/
        scp sqlite_web_interface.py ${USER}@${SERVER}:${REMOTE_PATH}/
        scp docker-compose.simple.yml ${USER}@${SERVER}:${REMOTE_PATH}/
        
        # 2. Server preparation
        Write-Status "Preparing configuration on server..."
        $prepCommand = "cd ${REMOTE_PATH}; mv docker-compose.simple.yml docker-compose.yml"
        ssh ${USER}@${SERVER} $prepCommand
        
        # 3. Stop old containers
        Write-Status "Stopping old containers..."
        $stopCommand = "cd ${REMOTE_PATH}; docker-compose down"
        ssh ${USER}@${SERVER} $stopCommand
        
        # 4. Build images
        Write-Status "Building new images..."
        $buildCommand = "cd ${REMOTE_PATH}; docker-compose build --no-cache"
        ssh ${USER}@${SERVER} $buildCommand
        
        # 5. Start containers
        Write-Status "Starting containers..."
        $startCommand = "cd ${REMOTE_PATH}; docker-compose up -d"
        ssh ${USER}@${SERVER} $startCommand
        
        # 6. Check status
        Write-Status "Checking container status..."
        $statusCommand = "cd ${REMOTE_PATH}; docker-compose ps"
        ssh ${USER}@${SERVER} $statusCommand
        
        # 7. Health check
        Write-Status "Waiting for services to start..."
        Start-Sleep -Seconds 10
        
        try {
            $healthResponse = Invoke-WebRequest -Uri "http://${SERVER}:5555/health" -UseBasicParsing -TimeoutSec 10
            if ($healthResponse.StatusCode -eq 200) {
                Write-Success "CareBot is working! Health check: OK"
            }
        }
        catch {
            Write-Error "CareBot health check failed: $($_.Exception.Message)"
        }
        
        try {
            $webResponse = Invoke-WebRequest -Uri "http://${SERVER}:8080" -UseBasicParsing -TimeoutSec 10
            if ($webResponse.StatusCode -eq 200) {
                Write-Success "SQLite Web is working! Available at http://${SERVER}:8080"
            }
        }
        catch {
            Write-Error "SQLite Web is not accessible: $($_.Exception.Message)"
        }
        
        Write-Success "Deployment completed!"
        Write-Host "📊 CareBot API: http://${SERVER}:5555" -ForegroundColor Yellow
        Write-Host "🗄️  SQLite Web: http://${SERVER}:8080" -ForegroundColor Yellow
    }
    
    "status" {
        Write-Status "Checking service status..."
        $statusCommand = "cd ${REMOTE_PATH}; docker-compose ps"
        ssh ${USER}@${SERVER} $statusCommand
        
        try {
            Invoke-WebRequest -Uri "http://${SERVER}:5555/health" -UseBasicParsing | Out-Null
            Write-Success "CareBot: WORKING"
        }
        catch {
            Write-Error "CareBot: NOT ACCESSIBLE"
        }
        
        try {
            Invoke-WebRequest -Uri "http://${SERVER}:8080" -UseBasicParsing | Out-Null
            Write-Success "SQLite Web: WORKING"
        }
        catch {
            Write-Error "SQLite Web: NOT ACCESSIBLE"
        }
    }
    
    "logs" {
        Write-Status "Showing CareBot logs..."
        $logsCommand = "cd ${REMOTE_PATH}; docker-compose logs carebot"
        ssh ${USER}@${SERVER} $logsCommand
    }
    
    "backup" {
        Write-Status "Creating manual database backup..."
        $backupCommand = "cd ${REMOTE_PATH}; ./scripts/backup-database.sh"
        ssh ${USER}@${SERVER} $backupCommand
        Write-Success "Backup completed"
    }
    
    "restore" {
        Write-Status "Restoring database from latest backup..."
        $restoreCommand = "cd ${REMOTE_PATH}; ./scripts/restore-database.sh"
        ssh ${USER}@${SERVER} $restoreCommand
        Write-Success "Restore completed"
    }
    
    "restart" {
        Write-Status "Restarting services..."
        $restartCommand = "cd ${REMOTE_PATH}; docker-compose restart"
        ssh ${USER}@${SERVER} $restartCommand
        Write-Success "Services restarted"
    }
    
    "stop" {
        Write-Status "Stopping services..."
        $stopCommand = "cd ${REMOTE_PATH}; docker-compose down"
        ssh ${USER}@${SERVER} $stopCommand
        Write-Success "Services stopped"
    }
    
    default {
        Write-Host "Usage: .\deploy-proven.ps1 [deploy|status|logs|backup|restore|restart|stop]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Cyan
        Write-Host "  deploy  - Full deployment (default)" -ForegroundColor White
        Write-Host "  status  - Check service status" -ForegroundColor White
        Write-Host "  logs    - View CareBot logs" -ForegroundColor White
        Write-Host "  backup  - Create manual backup" -ForegroundColor White
        Write-Host "  restore - Restore from latest backup" -ForegroundColor White
        Write-Host "  restart - Restart services" -ForegroundColor White
        Write-Host "  stop    - Stop services" -ForegroundColor White
    }
}
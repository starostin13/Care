# CareBot Production Deployment with SQLite Web Interface
# PowerShell script for deploying with database management tools

param(
    [string]$Action = "deploy",
    [string]$RemoteHost = "ubuntu@192.168.0.125",
    [string]$RemoteDir = "/home/ubuntu/carebot-production"
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "INFO: $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "SUCCESS: $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Deploy-CareBot {
    Write-Info "🚀 Starting CareBot deployment with SQLite Web interface..."
    
    # Check if Telegram token exists
    if (-not (Test-Path ".env")) {
        Write-Error "❌ .env file not found! Please create it with your Telegram token."
        exit 1
    }
    
    $tokenContent = Get-Content ".env" | Where-Object { $_ -like "TELEGRAM_TOKEN=*" }
    if (-not $tokenContent) {
        Write-Error "❌ TELEGRAM_TOKEN not found in .env file!"
        exit 1
    }
    
    $token = ($tokenContent -split "=")[1]
    if ($token.Length -lt 10) {
        Write-Error "❌ Invalid Telegram token in .env file!"
        exit 1
    }
    
    Write-Success "✅ Telegram token validated: $($token.Substring(0,10))..."
    
    Write-Info "📂 Creating remote directory structure..."
    ssh $RemoteHost "mkdir -p $RemoteDir/data"
    
    Write-Info "📤 Syncing files to server..."
    scp -r CareBot "$($RemoteHost):$RemoteDir/"
    scp docker-compose.sqlite-web.yml "$($RemoteHost):$RemoteDir/docker-compose.yml"
    scp Dockerfile.production "$($RemoteHost):$RemoteDir/CareBot/Dockerfile"
    scp .env "$($RemoteHost):$RemoteDir/"
    scp entrypoint.sh "$($RemoteHost):$RemoteDir/"
    
    Write-Info "🔧 Setting up permissions..."
    ssh $RemoteHost "chmod +x $RemoteDir/entrypoint.sh"
    
    Write-Info "🛑 Stopping existing services..."
    ssh $RemoteHost "cd $RemoteDir; docker-compose down" 2>$null
    
    Write-Info "🏗️ Building services..."
    ssh $RemoteHost "cd $RemoteDir; docker-compose build --no-cache"
    
    Write-Info "▶️ Starting services..."
    ssh $RemoteHost "cd $RemoteDir; docker-compose up -d"
    
    Write-Info "⏳ Waiting for services to initialize..."
    Start-Sleep -Seconds 15
    
    # Check service status
    Write-Info "🔍 Checking service status..."
    $servicesStatus = ssh $RemoteHost "cd $RemoteDir; docker-compose ps --format table"
    Write-Host $servicesStatus
    
    # Health checks
    Write-Info "🏥 Performing health checks..."
    
    try {
        ssh $RemoteHost "curl -f http://localhost:5555/health" 2>$null | Out-Null
        Write-Success "✅ CareBot is healthy!"
    }
    catch {
        Write-Error "❌ CareBot health check failed"
    }
    
    try {
        ssh $RemoteHost "curl -f http://localhost:8080" 2>$null | Out-Null
        Write-Success "✅ SQLite Web interface is running!"
    }
    catch {
        Write-Error "❌ SQLite Web interface health check failed"
    }
    
    Write-Success "✅ Deployment completed!"
    Write-Host ""
    Write-Host "🔗 Access Points:" -ForegroundColor Yellow
    Write-Host "   CareBot API:     http://192.168.0.125:5555" -ForegroundColor White
    Write-Host "   SQLite Web UI:   http://192.168.0.125:8080" -ForegroundColor White
    Write-Host "   Health Check:    http://192.168.0.125:5555/health" -ForegroundColor White
    Write-Host ""
    Write-Host "🛠️ Management Commands:" -ForegroundColor Yellow
    Write-Host "   View logs:    ssh $RemoteHost 'cd $RemoteDir && docker-compose logs -f'" -ForegroundColor White
    Write-Host "   Restart all:  ssh $RemoteHost 'cd $RemoteDir && docker-compose restart'" -ForegroundColor White
    Write-Host "   Stop all:     ssh $RemoteHost 'cd $RemoteDir && docker-compose down'" -ForegroundColor White
    Write-Host "   DB backup:    ssh $RemoteHost 'cd $RemoteDir; docker exec carebot_production sqlite3 /app/data/game_database.db `.backup backup_`$(Get-Date -Format yyyyMMdd_HHmmss).db`'" -ForegroundColor White
}

function Show-Status {
    Write-Info "📊 Checking CareBot status..."
    
    try {
        $status = ssh $RemoteHost "cd $RemoteDir; docker-compose ps --format table"
        Write-Host $status
        
        Write-Info "🏥 Health checks..."
        try {
            ssh $RemoteHost "curl -f http://localhost:5555/health" 2>$null | Out-Null
            Write-Success "✅ CareBot: Healthy"
        }
        catch {
            Write-Error "❌ CareBot: Unhealthy"
        }
        
        try {
            ssh $RemoteHost "curl -f http://localhost:8080" 2>$null | Out-Null
            Write-Success "✅ SQLite Web: Healthy"
        }
        catch {
            Write-Error "❌ SQLite Web: Unhealthy"
        }
        
    }
    catch {
        Write-Error "❌ Failed to connect to remote server"
    }
}

function Show-Logs {
    Write-Info "📋 Showing recent logs..."
    ssh $RemoteHost "cd $RemoteDir; docker-compose logs --tail=20"
}

function Backup-Database {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = "backup_$timestamp.db"
    
    Write-Info "💾 Creating database backup: $backupName"
    ssh $RemoteHost "cd $RemoteDir; docker exec carebot_production sqlite3 /app/data/game_database.db '.backup /app/data/$backupName'"
    Write-Success "✅ Backup created: $backupName"
}

# Main execution
switch ($Action.ToLower()) {
    "deploy" { Deploy-CareBot }
    "status" { Show-Status }
    "logs" { Show-Logs }
    "backup" { Backup-Database }
    default {
        Write-Host "Usage: .\deploy-sqlite-web.ps1 [deploy|status|logs|backup]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor White
        Write-Host "  deploy  - Deploy CareBot with SQLite Web interface" -ForegroundColor Gray
        Write-Host "  status  - Check service status and health" -ForegroundColor Gray
        Write-Host "  logs    - Show recent logs" -ForegroundColor Gray
        Write-Host "  backup  - Create database backup" -ForegroundColor Gray
    }
}
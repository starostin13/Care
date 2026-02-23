# Production deployment script for CareBot
param(
    [string]$Action = "deploy",
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 CareBot Production Deployment" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check .env file
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    exit 1
}

# Read token from .env
$envContent = Get-Content ".env"
$token = ($envContent | Where-Object { $_ -match "^TELEGRAM_BOT_TOKEN=(.+)" } | ForEach-Object { 
    if ($_ -match "^TELEGRAM_BOT_TOKEN=(.+)") { $matches[1] }
}) | Select-Object -First 1

if (-not $token) {
    Write-Host "❌ TELEGRAM_BOT_TOKEN not found in .env!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Token found: $($token.Substring(0, 10))..." -ForegroundColor Green

switch ($Action) {
    "deploy" {
        Write-Host "🚀 Starting production deployment..." -ForegroundColor Yellow
        
        # Copy files to server
        Write-Host "📁 Copying files to server..." -ForegroundColor Blue
        scp -r . ubuntu@192.168.1.125:/home/ubuntu/carebot-production/
        
        # Setup environment on server
        Write-Host "🔧 Setting up environment..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 @"
cd /home/ubuntu/carebot-production
echo 'TELEGRAM_BOT_TOKEN=$token' > .env
mkdir -p data logs
"@
        
        # Stop existing dev version (if running)
        Write-Host "🛑 Stopping development containers..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot; docker-compose down" 2>$null
        
        # Deploy production version
        Write-Host "🔨 Building production containers..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml down"
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml build --no-cache"
        
        Write-Host "🚀 Starting production services..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml up -d"
        
        Write-Host "⏳ Waiting for services to start..." -ForegroundColor Blue
        Start-Sleep 15
        
        # Check status
        Write-Host "🔍 Checking service status..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 "docker ps | grep carebot"
        
        Write-Host "✅ Production deployment completed!" -ForegroundColor Green
        Write-Host "🌐 Health check: http://192.168.1.125:5555/health" -ForegroundColor Cyan
        Write-Host "📊 Database viewer: http://192.168.1.125:8080 (with admin profile)" -ForegroundColor Cyan
    }
    
    "status" {
        Write-Host "📊 Production status..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml ps"
        
        Write-Host "`n🔍 Health check:" -ForegroundColor Blue
        try {
            $health = Invoke-WebRequest -Uri "http://192.168.1.125:5555/health" -TimeoutSec 10
            $healthData = $health.Content | ConvertFrom-Json
            Write-Host "✅ Status: $($health.StatusCode)" -ForegroundColor Green
            Write-Host "📊 Service: $($healthData.status)" -ForegroundColor Green
            Write-Host "🗄️ Database: $($healthData.database)" -ForegroundColor Green
            Write-Host "🕐 Timestamp: $($healthData.timestamp)" -ForegroundColor Green
        } catch {
            Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    "logs" {
        Write-Host "📋 Production logs..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 "docker logs carebot_production --tail 50 -f"
    }
    
    "restart" {
        Write-Host "🔄 Restarting production services..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 @"
cd /home/ubuntu/carebot-production
echo 'TELEGRAM_BOT_TOKEN=$token' > .env
docker-compose -f docker-compose.production.yml restart
"@
        Write-Host "✅ Restart completed!" -ForegroundColor Green
    }
    
    "backup" {
        Write-Host "💾 Creating database backup..." -ForegroundColor Yellow
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production && cp data/game_database.db backup_$timestamp.db"
        Write-Host "✅ Backup created: backup_$timestamp.db" -ForegroundColor Green
    }
    
    "admin" {
        Write-Host "🔧 Starting admin tools..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml --profile admin up -d"
        Write-Host "✅ Admin tools started!" -ForegroundColor Green
        Write-Host "📊 Database viewer: http://192.168.1.125:8080" -ForegroundColor Cyan
    }
    
    "stop" {
        Write-Host "🛑 Stopping production services..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml down"
        Write-Host "✅ Services stopped!" -ForegroundColor Green
    }
    
    default {
        Write-Host @"
Usage: ./deploy-production.ps1 [ACTION]

Actions:
  deploy    - Full production deployment (default)
  status    - Check service status and health
  logs      - Show real-time logs
  restart   - Restart services
  backup    - Create database backup
  admin     - Start admin tools (database viewer)
  stop      - Stop all services
"@ -ForegroundColor Yellow
    }
}
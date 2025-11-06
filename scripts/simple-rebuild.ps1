#!/usr/bin/env pwsh
# Complete Production Rebuild Script for CareBot

param(
    [string]$Action = "rebuild"
)

$ErrorActionPreference = "Stop"
$SERVER = "ubuntu@192.168.1.125"
$PROJECT_ROOT = "C:\Users\staro\Projects\Care"
$ENV_FILE = "$PROJECT_ROOT\.env"

Write-Host "🚀 CareBot Production Rebuild" -ForegroundColor Green

# Get Telegram token
if (-not (Test-Path $ENV_FILE)) {
    Write-Error "❌ .env file not found"
    exit 1
}

$content = Get-Content $ENV_FILE
$tokenLine = $content | Where-Object { $_ -match "^TELEGRAM_BOT_TOKEN=" }
if (-not $tokenLine) {
    Write-Error "❌ Token not found in .env"
    exit 1
}

$token = $tokenLine.Split('=')[1].Trim('"')
Write-Host "✅ Token found: $($token.Substring(0,10))..." -ForegroundColor Green

switch ($Action.ToLower()) {
    "rebuild" {
        Write-Host "🛑 Stopping production..." -ForegroundColor Yellow
        ssh $SERVER "cd /home/ubuntu; docker-compose -f docker-compose.production.yml down 2>/dev/null || true"
        
        Write-Host "🗑️ Cleaning old images..." -ForegroundColor Yellow
        ssh $SERVER "docker container prune -f; docker image prune -f; docker rmi care-carebot-production 2>/dev/null || true"
        
        Write-Host "📁 Syncing files..." -ForegroundColor Blue
        ssh $SERVER "mkdir -p /home/ubuntu"
        
        # Use scp instead of rsync for Windows compatibility
        Write-Host "🔄 Copying project files..." -ForegroundColor Cyan
        ssh $SERVER "rm -rf /home/ubuntu/care_project"
        scp -r "$PROJECT_ROOT" "$SERVER`:~/care_project"
        
        Write-Host "🔧 Building image..." -ForegroundColor Blue
        ssh $SERVER "cd /home/ubuntu/care_project; TELEGRAM_BOT_TOKEN='$token' docker-compose -f docker-compose.production.yml build --no-cache"
        
        Write-Host "🚀 Starting production..." -ForegroundColor Blue
        ssh $SERVER "cd /home/ubuntu/care_project; TELEGRAM_BOT_TOKEN='$token' docker-compose -f docker-compose.production.yml up -d"
        
        Write-Host "⏳ Waiting for startup..." -ForegroundColor Yellow
        Start-Sleep -Seconds 20
        
        Write-Host "🏥 Testing health..." -ForegroundColor Blue
        $healthCheck = ssh $SERVER "curl -f http://localhost:5555/health 2>/dev/null || echo 'FAILED'"
        
        if ($healthCheck -match "healthy") {
            Write-Host "✅ REBUILD SUCCESSFUL!" -ForegroundColor Green
            Write-Host "🧪 Ready for testing - use: .\scripts\simple-rebuild.ps1 test" -ForegroundColor Yellow
        } else {
            Write-Host "❌ Health check failed" -ForegroundColor Red
            ssh $SERVER "cd /home/ubuntu/care_project; docker-compose -f docker-compose.production.yml logs --tail=10"
        }
    }
    
    "test" {
        Write-Host "🧪 Starting real-time log monitoring..." -ForegroundColor Blue
        Write-Host "Test the Settings button now!" -ForegroundColor Yellow
        ssh $SERVER "docker logs -f carebot_production"
    }
    
    "logs" {
        ssh $SERVER "cd /home/ubuntu/care_project; docker-compose -f docker-compose.production.yml logs --tail=30"
    }
    
    "status" {
        $health = ssh $SERVER "curl -f http://localhost:5555/health 2>/dev/null || echo 'FAILED'"
        $tables = ssh $SERVER "docker exec carebot_production sqlite3 /app/data/game_database.db '.tables' 2>/dev/null || echo 'DB_ERROR'"
        
        Write-Host "Health: $health" -ForegroundColor $(if($health -match "healthy") { "Green" } else { "Red" })
        Write-Host "Database: $tables" -ForegroundColor $(if($tables -match "warmasters") { "Green" } else { "Red" })
    }
    
    default {
        Write-Host "Usage: .\scripts\simple-rebuild.ps1 [rebuild|test|logs|status]" -ForegroundColor Yellow
    }
}
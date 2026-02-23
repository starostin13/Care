# Simple production deployment script for CareBot
param(
    [string]$Action = "deploy"
)

$ErrorActionPreference = "Stop"

Write-Host "Production CareBot Deployment" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Check .env file
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    exit 1
}

# Read token from .env
$envContent = Get-Content ".env"
$token = ($envContent | Where-Object { $_ -match "^TELEGRAM_BOT_TOKEN=(.+)" } | ForEach-Object { 
    if ($_ -match "^TELEGRAM_BOT_TOKEN=(.+)") { $matches[1] }
}) | Select-Object -First 1

if (-not $token) {
    Write-Host "ERROR: TELEGRAM_BOT_TOKEN not found in .env!" -ForegroundColor Red
    exit 1
}

Write-Host "Token found: $($token.Substring(0, 10))..." -ForegroundColor Green

switch ($Action) {
    "deploy" {
        Write-Host "Starting production deployment..." -ForegroundColor Yellow
        
        # Copy files to server
        Write-Host "Copying files to server..." -ForegroundColor Blue
        scp -r . ubuntu@192.168.1.125:/home/ubuntu/carebot-production/
        
        # Setup environment on server
        Write-Host "Setting up environment..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production"
        ssh ubuntu@192.168.1.125 "echo 'TELEGRAM_BOT_TOKEN=$token' > /home/ubuntu/carebot-production/.env"
        ssh ubuntu@192.168.1.125 "mkdir -p /home/ubuntu/carebot-production/data"
        ssh ubuntu@192.168.1.125 "mkdir -p /home/ubuntu/carebot-production/logs"
        
        # Stop existing containers
        Write-Host "Stopping existing containers..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot; docker-compose down" 2>$null
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml down" 2>$null
        
        # Build and start production
        Write-Host "Building production containers..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml build --no-cache"
        
        Write-Host "Starting production services..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml up -d"
        
        Write-Host "Waiting for services to start..." -ForegroundColor Blue
        Start-Sleep 15
        
        Write-Host "Checking service status..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 "docker ps | grep carebot"
        
        Write-Host "Production deployment completed!" -ForegroundColor Green
        Write-Host "Health check: http://192.168.1.125:5555/health" -ForegroundColor Cyan
    }
    
    "status" {
        Write-Host "Production status..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml ps"
        
        Write-Host "Health check:" -ForegroundColor Blue
        try {
            $health = Invoke-WebRequest -Uri "http://192.168.1.125:5555/health" -TimeoutSec 10
            $healthData = $health.Content | ConvertFrom-Json
            Write-Host "Status: $($health.StatusCode)" -ForegroundColor Green
            Write-Host "Service: $($healthData.status)" -ForegroundColor Green  
            Write-Host "Database: $($healthData.database)" -ForegroundColor Green
        } catch {
            Write-Host "Health check failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    "logs" {
        Write-Host "Production logs..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 "docker logs carebot_production --tail 50 -f"
    }
    
    "restart" {
        Write-Host "Restarting production services..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 "echo 'TELEGRAM_BOT_TOKEN=$token' > /home/ubuntu/carebot-production/.env"
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml restart"
        Write-Host "Restart completed!" -ForegroundColor Green
    }
    
    "stop" {
        Write-Host "Stopping production services..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production; docker-compose -f docker-compose.production.yml down"
        Write-Host "Services stopped!" -ForegroundColor Green
    }
    
    default {
        Write-Host "Usage: ./deploy-production-simple.ps1 [deploy|status|logs|restart|stop]" -ForegroundColor Yellow
    }
}
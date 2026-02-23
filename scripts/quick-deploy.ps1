# CareBot Quick Deploy Script
param(
    [string]$Action = "deploy"
)

$ErrorActionPreference = "Stop"

Write-Host "CareBot Quick Deploy Script" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan

# Check .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Create .env file with TELEGRAM_BOT_TOKEN" -ForegroundColor Yellow
    exit 1
}

# Read token from .env
$envContent = Get-Content ".env"
$token = ($envContent | Where-Object { $_ -match "^TELEGRAM_BOT_TOKEN=(.+)" } | ForEach-Object { 
    if ($_ -match "^TELEGRAM_BOT_TOKEN=(.+)") { $matches[1] }
}) | Select-Object -First 1

if (-not $token -or $token -eq "вставьте_ваш_токен_сюда") {
    Write-Host "ERROR: Token not set in .env file!" -ForegroundColor Red
    Write-Host "Edit .env and set correct TELEGRAM_BOT_TOKEN" -ForegroundColor Yellow
    exit 1
}

Write-Host "Token found: $($token.Substring(0, 10))..." -ForegroundColor Green

switch ($Action) {
    "deploy" {
        Write-Host "Starting full deploy..." -ForegroundColor Yellow
        
        # Copy files to server
        Write-Host "Copying files to server..." -ForegroundColor Blue
        scp -r . ubuntu@192.168.1.125:/home/ubuntu/carebot/
        
        # Create .env on server
        Write-Host "Setting up token on server..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot; echo 'TELEGRAM_BOT_TOKEN=$token' > .env"
        
        # Rebuild and start
        Write-Host "Rebuilding container..." -ForegroundColor Blue
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot; docker-compose down"
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot; docker-compose build --no-cache"
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot; docker-compose up -d"
        
        Write-Host "Deploy completed!" -ForegroundColor Green
        Write-Host "Health check: http://192.168.1.125:5555/health" -ForegroundColor Cyan
    }
    
    "restart" {
        Write-Host "Restarting container..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot; echo 'TELEGRAM_BOT_TOKEN=$token' > .env"
        ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot; docker-compose restart"
        Write-Host "Restart completed!" -ForegroundColor Green
    }
    
    "logs" {
        Write-Host "Showing logs..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 "docker logs carebot_carebot_1 --tail 50 -f"
    }
    
    "status" {
        Write-Host "Service status..." -ForegroundColor Yellow
        ssh ubuntu@192.168.1.125 "docker ps"
        Write-Host "`nHealth check:" -ForegroundColor Blue
        try {
            $health = Invoke-WebRequest -Uri "http://192.168.1.125:5555/health" -TimeoutSec 5
            Write-Host "Status: $($health.StatusCode)" -ForegroundColor Green
        } catch {
            Write-Host "Health check failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    default {
        Write-Host "Usage: ./quick-deploy.ps1 [deploy|restart|logs|status]" -ForegroundColor Yellow
    }
}
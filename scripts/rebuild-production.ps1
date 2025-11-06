#!/usr/bin/env pwsh
# Comprehensive production rebuild script for CareBot
# This script performs a complete rebuild and deployment

param(
    [string]$Action = "rebuild"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting CareBot Production Rebuild" -ForegroundColor Green
Write-Host "Action: $Action" -ForegroundColor Yellow
Write-Host "=" * 50

# Configuration
$SERVER = "ubuntu@192.168.1.125"
$PROJECT_ROOT = "C:\Users\staro\Projects\Care"
$ENV_FILE = "$PROJECT_ROOT\.env"

function Get-TelegramToken {
    if (-not (Test-Path $ENV_FILE)) {
        Write-Error "❌ .env file not found at $ENV_FILE"
        exit 1
    }
    
    $content = Get-Content $ENV_FILE
    $tokenLine = $content | Where-Object { $_ -match "^TELEGRAM_BOT_TOKEN=" }
    
    if (-not $tokenLine) {
        Write-Error "❌ TELEGRAM_BOT_TOKEN not found in .env file"
        exit 1
    }
    
    $token = $tokenLine.Split('=')[1].Trim('"')
    if ($token.Length -lt 10) {
        Write-Error "❌ Invalid token format"
        exit 1
    }
    
    Write-Host "✅ Token found: $($token.Substring(0,10))..." -ForegroundColor Green
    return $token
}

function Test-FileStructure {
    Write-Host "🔍 Verifying file structure..." -ForegroundColor Blue
    
    $requiredFiles = @(
        "CareBot\run_hybrid.py",
        "CareBot\CareBot\handlers.py",
        "CareBot\CareBot\keyboard_constructor.py",
        "CareBot\CareBot\settings_helper.py",
        "CareBot\CareBot\sqllite_helper.py",
        "CareBot\CareBot\migrate_db.py",
        "CareBot\requirements.txt",
        "Dockerfile.production",
        "docker-compose.production.yml",
        "entrypoint.sh"
    )
    
    $missingFiles = @()
    foreach ($file in $requiredFiles) {
        $fullPath = Join-Path $PROJECT_ROOT $file
        if (-not (Test-Path $fullPath)) {
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Error "❌ Missing files: $($missingFiles -join ', ')"
        exit 1
    }
    
    Write-Host "✅ All required files present" -ForegroundColor Green
}

function Verify-CodeChanges {
    Write-Host "🔍 Verifying critical code fixes..." -ForegroundColor Blue
    
    # Check keyboard_constructor.py for proper imports
    $keyboardFile = "$PROJECT_ROOT\CareBot\CareBot\keyboard_constructor.py"
    $content = Get-Content $keyboardFile -Raw
    
    if ($content -match "sqllite_helper\.get_settings") {
        Write-Error "❌ keyboard_constructor.py still contains direct sqllite_helper calls"
        exit 1
    }
    
    if ($content -notmatch "settings_helper\.get_user_settings") {
        Write-Error "❌ keyboard_constructor.py missing settings_helper calls"
        exit 1
    }
    
    # Check migrate_db.py for environment variable usage
    $migrateFile = "$PROJECT_ROOT\CareBot\CareBot\migrate_db.py"
    $migrateContent = Get-Content $migrateFile -Raw
    
    if ($migrateContent -notmatch "DATABASE_PATH.*environ") {
        Write-Error "❌ migrate_db.py not using environment variables"
        exit 1
    }
    
    Write-Host "✅ Code fixes verified" -ForegroundColor Green
}

function Stop-Production {
    Write-Host "🛑 Stopping production services..." -ForegroundColor Yellow
    
    ssh $SERVER "cd /home/ubuntu; docker-compose -f docker-compose.production.yml down"
    
    Write-Host "✅ Production services stopped" -ForegroundColor Green
}

function Remove-OldImages {
    Write-Host "🗑️ Removing old Docker images..." -ForegroundColor Yellow
    
    # Remove old containers and images
    ssh $SERVER "docker container prune -f"
    ssh $SERVER "docker image prune -f"
    ssh $SERVER "docker rmi care-carebot-production 2>/dev/null || true"
    
    Write-Host "✅ Old images removed" -ForegroundColor Green
}

function Sync-AllFiles {
    Write-Host "📁 Syncing all project files..." -ForegroundColor Blue
    
    # Create remote directory
    ssh $SERVER "mkdir -p /home/ubuntu"
    
    # Sync entire project structure
    $excludePatterns = @(
        "--exclude=.git",
        "--exclude=.vs",
        "--exclude=__pycache__",
        "--exclude=*.pyc",
        "--exclude=.pytest_cache",
        "--exclude=node_modules",
        "--exclude=obj",
        "--exclude=bin"
    )
    
    $rsyncCmd = "rsync -avz --delete $($excludePatterns -join ' ') '$PROJECT_ROOT/' $SERVER"":~/care_project/"
    Invoke-Expression $rsyncCmd
    
    Write-Host "✅ All files synced" -ForegroundColor Green
}

function Build-Production {
    Write-Host "🔧 Building production Docker image..." -ForegroundColor Blue
    
    $token = Get-TelegramToken
    
    # Build with no cache to ensure fresh build
    ssh $SERVER "cd /home/ubuntu/care_project; TELEGRAM_BOT_TOKEN='$token' docker-compose -f docker-compose.production.yml build --no-cache"
    
    Write-Host "✅ Production image built" -ForegroundColor Green
}

function Start-Production {
    Write-Host "🚀 Starting production services..." -ForegroundColor Blue
    
    $token = Get-TelegramToken
    
    ssh $SERVER "cd /home/ubuntu/care_project; TELEGRAM_BOT_TOKEN='$token' docker-compose -f docker-compose.production.yml up -d"
    
    Write-Host "✅ Production services started" -ForegroundColor Green
}

function Test-Health {
    Write-Host "🏥 Testing application health..." -ForegroundColor Blue
    
    # Wait for application to start
    Start-Sleep -Seconds 15
    
    $maxRetries = 6
    $retryCount = 0
    
    while ($retryCount -lt $maxRetries) {
        try {
            $response = ssh $SERVER "curl -f http://localhost:5555/health 2>/dev/null"
            if ($response -match "healthy") {
                Write-Host "✅ Application is healthy!" -ForegroundColor Green
                return $true
            }
        }
        catch {
            # Ignore curl errors
        }
        
        $retryCount++
        Write-Host "⏳ Waiting for health check... ($retryCount/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }
    
    Write-Error "❌ Health check failed after $maxRetries attempts"
    return $false
}

function Show-Logs {
    Write-Host "📋 Showing recent logs..." -ForegroundColor Blue
    
    ssh $SERVER "cd /home/ubuntu/care_project; docker-compose -f docker-compose.production.yml logs --tail=20"
}

function Verify-Database {
    Write-Host "🗄️ Verifying database structure..." -ForegroundColor Blue
    
    $tablesCheck = ssh $SERVER "docker exec carebot_production sqlite3 /app/data/game_database.db '.tables' 2>/dev/null"
    
    if ($tablesCheck -match "warmasters") {
        Write-Host "✅ Database tables verified" -ForegroundColor Green
    } else {
        Write-Warning "⚠️ Database tables not found - checking initialization..."
        ssh $SERVER "docker exec carebot_production ls -la /app/data/"
    }
}

function Test-Settings {
    Write-Host "🧪 Testing Settings functionality..." -ForegroundColor Blue
    Write-Host "Please test the bot manually:" -ForegroundColor Yellow
    Write-Host "1. Send /start command" -ForegroundColor Cyan
    Write-Host "2. Click Settings button" -ForegroundColor Cyan
    Write-Host "3. Verify language and notification buttons appear" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Monitoring logs in real-time (Ctrl+C to stop)..." -ForegroundColor Yellow
    
    ssh $SERVER "docker logs -f carebot_production"
}

# Main execution
switch ($Action.ToLower()) {
    "rebuild" {
        Test-FileStructure
        Verify-CodeChanges
        Stop-Production
        Remove-OldImages
        Sync-AllFiles
        Build-Production
        Start-Production
        if (Test-Health) {
            Verify-Database
            Write-Host ""
            Write-Host "🎉 REBUILD COMPLETED SUCCESSFULLY!" -ForegroundColor Green
            Write-Host "Ready for testing!" -ForegroundColor Yellow
        }
    }
    "test" {
        Test-Settings
    }
    "logs" {
        Show-Logs
    }
    "status" {
        Test-Health
        Verify-Database
    }
    default {
        Write-Host "Usage: .\rebuild-production.ps1 [rebuild|test|logs|status]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Cyan
        Write-Host "  rebuild - Complete rebuild and deployment (default)" -ForegroundColor White
        Write-Host "  test    - Start real-time log monitoring for testing" -ForegroundColor White
        Write-Host "  logs    - Show recent logs" -ForegroundColor White
        Write-Host "  status  - Check health and database status" -ForegroundColor White
    }
}
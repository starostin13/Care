# CareBot Production Update Script
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

# Check token
function Test-Token {
    Write-Info "Checking Telegram token..."
    
    if (-not (Test-Path $LOCAL_ENV_FILE)) {
        Write-Error "File $LOCAL_ENV_FILE not found!"
        return $false
    }
    
    $token = Get-Content $LOCAL_ENV_FILE | Where-Object { $_ -match "TELEGRAM_BOT_TOKEN=" } | ForEach-Object { $_.Split('=')[1] }
    
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
        "CareBot/CareBot/warmaster_helper.py", 
        "CareBot/CareBot/settings_helper.py",
        "CareBot/CareBot/schedule_helper.py",
        "CareBot/CareBot/mission_helper.py",
        "CareBot/CareBot/players_helper.py",
        "CareBot/CareBot/map_helper.py",
        "CareBot/CareBot/sqllite_helper.py",
        "CareBot/CareBot/keyboard_constructor.py",
        "CareBot/CareBot/localization.py",
        "CareBot/CareBot/notification_service.py",
        "CareBot/CareBot/migrate_db.py",
        "CareBot/requirements.txt"
    )
    
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
    
    Write-Success "File sync completed"
    return $true
}

# Test health check
function Test-Health {
    Write-Info "Checking service health..."
    
    Start-Sleep -Seconds 10
    
    try {
        $response = Invoke-WebRequest -Uri $HEALTH_URL -Method GET -TimeoutSec 10
        
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

# Update production
function Update-Production {
    Write-Host "Starting CareBot Production Update" -ForegroundColor Yellow
    
    if (-not (Test-Token)) { return $false }
    
    if (-not (Sync-Files)) { return $false }
    
    Write-Info "Restarting production service..."
    ssh $SERVER_HOST "cd $PRODUCTION_PATH; docker-compose -f docker-compose.production.yml restart"
    
    if (-not $SkipHealthCheck) {
        Test-Health
    }
    
    Write-Success "Update completed!"
    return $true
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
        ssh $SERVER_HOST "cd $PRODUCTION_PATH; docker-compose -f docker-compose.production.yml logs --tail=20"
    }
    default {
        Write-Host ""
        Write-Host "CareBot Production Update Script" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Usage: .\scripts\update-production.ps1 [action]"
        Write-Host ""
        Write-Host "Actions:"
        Write-Host "  update  - Update production (default)"
        Write-Host "  status  - Check health"
        Write-Host "  logs    - Show logs"
        Write-Host ""
        Write-Host "Options:"
        Write-Host "  -Force           - Skip confirmations"
        Write-Host "  -SkipHealthCheck - Skip health check"
    }
}
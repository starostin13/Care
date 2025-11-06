# Simple CareBot Deployment Script
param(
    [string]$Action = "deploy"
)

$RemoteHost = "ubuntu@192.168.0.125"
$RemoteDir = "/home/ubuntu/carebot"

function Write-Info { param([string]$Message); Write-Host "INFO: $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message); Write-Host "SUCCESS: $Message" -ForegroundColor Green }

switch ($Action.ToLower()) {
    "deploy" {
        Write-Info "🚀 Deploying CareBot..."
        
        # Copy files
        Write-Info "📤 Copying files..."
        ssh $RemoteHost "mkdir -p $RemoteDir/data"
        scp -r CareBot "$($RemoteHost):$RemoteDir/"
        scp sqlite_web_interface.py "$($RemoteHost):$RemoteDir/"
        scp Dockerfile.carebot "$($RemoteHost):$RemoteDir/"
        scp Dockerfile.sqlite-web "$($RemoteHost):$RemoteDir/"
        scp docker-compose.simple.yml "$($RemoteHost):$RemoteDir/docker-compose.yml"
        scp .env "$($RemoteHost):$RemoteDir/"
        
        # Deploy
        Write-Info "🏗️ Building and starting..."
        ssh $RemoteHost "cd $RemoteDir; docker-compose down"
        ssh $RemoteHost "cd $RemoteDir; docker-compose build --no-cache"
        ssh $RemoteHost "cd $RemoteDir; docker-compose up -d"
        
        Write-Success "✅ Deployment completed!"
        Write-Host ""
        Write-Host "🔗 Access Points:" -ForegroundColor Yellow
        Write-Host "   CareBot API:     http://192.168.0.125:5555" -ForegroundColor White
        Write-Host "   SQLite Web UI:   http://192.168.0.125:8080" -ForegroundColor White
    }
    "status" {
        Write-Info "📊 Checking status..."
        ssh $RemoteHost "cd $RemoteDir; docker-compose ps"
    }
    "logs" {
        Write-Info "📋 Showing logs..."
        ssh $RemoteHost "cd $RemoteDir; docker-compose logs --tail=20"
    }
    "restart" {
        Write-Info "🔄 Restarting services..."
        ssh $RemoteHost "cd $RemoteDir; docker-compose restart"
    }
    default {
        Write-Host "Usage: .\deploy-simple.ps1 [deploy|status|logs|restart]"
    }
}
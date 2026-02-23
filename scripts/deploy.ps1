# CareBot Deployment Script for Windows
# This script deploys the CareBot application to Ubuntu server

param(
    [string]$RemoteHost = "192.168.1.125",
    [string]$RemoteUser = "ubuntu",
    [string]$ImageName = "carebot",
    [string]$ContainerName = "carebot-app"
)

$ErrorActionPreference = "Stop"

Write-Host "Starting CareBot deployment..." -ForegroundColor Green

try {
    # Build Docker image
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    docker build -t $ImageName .
    
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed"
    }

    # Save image to tar file
    Write-Host "Saving Docker image..." -ForegroundColor Yellow
    docker save $ImageName -o carebot.tar
    
    if ($LASTEXITCODE -ne 0) {
        throw "Docker save failed"
    }

    # Copy files to remote server using scp
    Write-Host "Copying files to remote server..." -ForegroundColor Yellow
    
    # Ensure remote directory exists
    ssh "$RemoteUser@$RemoteHost" "mkdir -p /home/ubuntu/carebot"
    
    # Copy files
    scp carebot.tar "$RemoteUser@$RemoteHost":/home/ubuntu/carebot/
    scp docker-compose.yml "$RemoteUser@$RemoteHost":/home/ubuntu/carebot/
    scp scripts/remote-deploy.sh "$RemoteUser@$RemoteHost":/home/ubuntu/carebot/

    # Execute deployment on remote server
    Write-Host "Executing deployment on remote server..." -ForegroundColor Yellow
    ssh "$RemoteUser@$RemoteHost" "cd /home/ubuntu/carebot && chmod +x remote-deploy.sh && ./remote-deploy.sh"

    # Cleanup local tar file
    Remove-Item carebot.tar -ErrorAction SilentlyContinue

    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host "Application should be available at http://$RemoteHost:5555" -ForegroundColor Cyan

    # Test connection
    Write-Host "Testing connection..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://$RemoteHost:5555/health" -TimeoutSec 10 -ErrorAction Stop
        Write-Host "Health check passed!" -ForegroundColor Green
    }
    catch {
        Write-Host "Health check failed - please check logs manually" -ForegroundColor Red
        Write-Host "You can check logs with: ssh $RemoteUser@$RemoteHost 'docker logs carebot-app'" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    
    # Cleanup on failure
    if (Test-Path "carebot.tar") {
        Remove-Item carebot.tar -ErrorAction SilentlyContinue
    }
    
    exit 1
}

Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  Check logs: ssh $RemoteUser@$RemoteHost 'docker logs $ContainerName'" -ForegroundColor White
Write-Host "  Restart app: ssh $RemoteUser@$RemoteHost 'cd /home/ubuntu/carebot && docker-compose restart'" -ForegroundColor White
Write-Host "  Stop app: ssh $RemoteUser@$RemoteHost 'cd /home/ubuntu/carebot && docker-compose down'" -ForegroundColor White
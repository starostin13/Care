# Hybrid deployment script - uses Docker on remote server
# This script builds and deploys without requiring Docker on local machine

param(
    [string]$RemoteHost = "192.168.1.125",
    [string]$RemoteUser = "ubuntu",
    [string]$AppName = "carebot"
)

$ErrorActionPreference = "Stop"

Write-Host "Starting hybrid CareBot deployment..." -ForegroundColor Green

try {
    # Copy application files to remote server
    Write-Host "Copying application files to remote server..." -ForegroundColor Yellow
    
    # Ensure remote directory exists
    ssh "$RemoteUser@$RemoteHost" "mkdir -p /home/ubuntu/carebot"
    
    # Copy project files
    scp -r .\CareBot\* "$RemoteUser@$RemoteHost":/home/ubuntu/carebot/
    scp .\Dockerfile "$RemoteUser@$RemoteHost":/home/ubuntu/carebot/
    scp .\docker-compose.yml "$RemoteUser@$RemoteHost":/home/ubuntu/carebot/
    scp .\.dockerignore "$RemoteUser@$RemoteHost":/home/ubuntu/carebot/
    
    # Build and run Docker container on remote server
    Write-Host "Building Docker image on remote server..." -ForegroundColor Yellow
    
    # Check if Docker is installed on remote server
    $dockerCheck = ssh "$RemoteUser@$RemoteHost" "which docker" 2>$null
    if (-not $dockerCheck) {
        Write-Host "Installing Docker on remote server..." -ForegroundColor Yellow
        ssh "$RemoteUser@$RemoteHost" @"
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu
"@
        Write-Host "Docker installed. You may need to logout/login on the server for group changes to take effect." -ForegroundColor Yellow
        Write-Host "Continuing with sudo docker commands..." -ForegroundColor Yellow
        $dockerCmd = "sudo docker"
        $composeCmd = "sudo docker-compose"
    } else {
        $dockerCmd = "docker"
        $composeCmd = "docker-compose"
    }
    
    # Stop existing containers
    Write-Host "Stopping existing containers..." -ForegroundColor Yellow
    ssh "$RemoteUser@$RemoteHost" "cd /home/ubuntu/carebot && $composeCmd down 2>/dev/null || true"
    
    # Build new image
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    ssh "$RemoteUser@$RemoteHost" "cd /home/ubuntu/carebot && $dockerCmd build -t carebot ."
    
    # Start services
    Write-Host "Starting services..." -ForegroundColor Yellow
    ssh "$RemoteUser@$RemoteHost" "cd /home/ubuntu/carebot && $composeCmd up -d"
    
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host "Application should be available at http://$RemoteHost:5555" -ForegroundColor Cyan
    
    # Wait a moment for container to start
    Write-Host "Waiting for application to start..." -ForegroundColor Yellow
    Start-Sleep 10
    
    # Test connection
    Write-Host "Testing connection..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://$RemoteHost:5555/health" -TimeoutSec 10 -ErrorAction Stop
        $health = $response.Content | ConvertFrom-Json
        Write-Host "Health check passed!" -ForegroundColor Green
        Write-Host "Status: $($health.status)" -ForegroundColor White
        Write-Host "Database: $($health.database)" -ForegroundColor White
    }
    catch {
        Write-Host "Health check failed - checking container status..." -ForegroundColor Red
        ssh "$RemoteUser@$RemoteHost" "cd /home/ubuntu/carebot && $dockerCmd ps -a"
        Write-Host ""
        Write-Host "Container logs:" -ForegroundColor Yellow
        ssh "$RemoteUser@$RemoteHost" "cd /home/ubuntu/carebot && $dockerCmd logs carebot-carebot-1 --tail 20"
    }
}
catch {
    Write-Host "Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  Check status: ssh $RemoteUser@$RemoteHost 'cd /home/ubuntu/carebot && docker ps'" -ForegroundColor White
Write-Host "  View logs: ssh $RemoteUser@$RemoteHost 'cd /home/ubuntu/carebot && docker logs carebot-carebot-1'" -ForegroundColor White
Write-Host "  Restart: ssh $RemoteUser@$RemoteHost 'cd /home/ubuntu/carebot && docker-compose restart'" -ForegroundColor White
Write-Host "  Stop: ssh $RemoteUser@$RemoteHost 'cd /home/ubuntu/carebot && docker-compose down'" -ForegroundColor White
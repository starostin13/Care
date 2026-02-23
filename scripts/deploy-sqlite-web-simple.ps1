# CareBot Production Deployment with SQLite Web Interface

param(
    [string]$Action = "deploy"
)

$RemoteHost = "ubuntu@192.168.0.125"
$RemoteDir = "/home/ubuntu/carebot-production"

function Write-Info { param([string]$Message); Write-Host "INFO: $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message); Write-Host "SUCCESS: $Message" -ForegroundColor Green }
function Write-Error { param([string]$Message); Write-Host "ERROR: $Message" -ForegroundColor Red }

if ($Action -eq "deploy") {
    Write-Info "🚀 Starting CareBot deployment with SQLite Web interface..."
    
    # Validate .env file
    if (-not (Test-Path ".env")) {
        Write-Error "❌ .env file not found!"
        exit 1
    }
    
    Write-Info "📂 Creating remote directory..."
    ssh $RemoteHost "mkdir -p $RemoteDir/data"
    
    Write-Info "📤 Copying files..."
    scp -r CareBot "$($RemoteHost):$RemoteDir/"
    scp docker-compose.sqlite-web.yml "$($RemoteHost):$RemoteDir/docker-compose.yml"
    scp Dockerfile.production "$($RemoteHost):$RemoteDir/CareBot/Dockerfile"
    scp .env "$($RemoteHost):$RemoteDir/"
    scp entrypoint.sh "$($RemoteHost):$RemoteDir/"
    
    Write-Info "🔧 Setting permissions..."
    ssh $RemoteHost "chmod +x $RemoteDir/entrypoint.sh"
    
    Write-Info "🛑 Stopping services..."
    ssh $RemoteHost "cd $RemoteDir; docker-compose down" 2>$null
    
    Write-Info "🏗️ Building..."
    ssh $RemoteHost "cd $RemoteDir; docker-compose build --no-cache"
    
    Write-Info "▶️ Starting..."
    ssh $RemoteHost "cd $RemoteDir; docker-compose up -d"
    
    Start-Sleep -Seconds 15
    
    Write-Success "✅ Deployment completed!"
    Write-Host ""
    Write-Host "🔗 Access Points:" -ForegroundColor Yellow
    Write-Host "   CareBot API:     http://192.168.0.125:5555" -ForegroundColor White
    Write-Host "   SQLite Web UI:   http://192.168.0.125:8080" -ForegroundColor White
}
elseif ($Action -eq "status") {
    Write-Info "📊 Checking status..."
    ssh $RemoteHost "cd $RemoteDir; docker-compose ps"
}
elseif ($Action -eq "logs") {
    Write-Info "📋 Showing logs..."
    ssh $RemoteHost "cd $RemoteDir; docker-compose logs --tail=20"
}
else {
    Write-Host "Usage: .\deploy-sqlite-web.ps1 [deploy|status|logs]"
}
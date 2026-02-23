# Direct deployment script without Docker
# Deploys Python application directly to Ubuntu server

param(
    [string]$RemoteHost = "192.168.1.125",
    [string]$RemoteUser = "ubuntu",
    [string]$AppName = "carebot"
)

$ErrorActionPreference = "Stop"

Write-Host "Starting direct CareBot deployment..." -ForegroundColor Green

try {
    # Create deployment package
    Write-Host "Creating deployment package..." -ForegroundColor Yellow
    
    # Create temp directory for packaging
    $tempDir = ".\temp_deploy"
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempDir
    
    # Copy application files
    Copy-Item -Path ".\CareBot\*" -Destination $tempDir -Recurse
    Copy-Item -Path ".\agents.md" -Destination $tempDir
    Copy-Item -Path ".\DEPLOYMENT.md" -Destination $tempDir
    
    # Create a simple service script
    $serviceScript = @"
#!/bin/bash
# CareBot service script

APP_DIR="/home/ubuntu/carebot"
VENV_DIR="`$APP_DIR/venv"
PID_FILE="`$APP_DIR/carebot.pid"

case "`$1" in
    start)
        echo "Starting CareBot..."
        cd `$APP_DIR
        if [ ! -d "`$VENV_DIR" ]; then
            python3 -m venv venv
            source venv/bin/activate
            pip install -r requirements.txt
        else
            source venv/bin/activate
        fi
        
        export DATABASE_PATH="`$APP_DIR/data/game_database.db"
        export SERVER_HOST="0.0.0.0"
        export SERVER_PORT="5555"
        
        mkdir -p data
        nohup python runserver.py > logs/app.log 2>&1 &
        echo `$! > `$PID_FILE
        echo "CareBot started with PID `$(cat `$PID_FILE)"
        ;;
    stop)
        echo "Stopping CareBot..."
        if [ -f "`$PID_FILE" ]; then
            kill `$(cat `$PID_FILE)
            rm `$PID_FILE
            echo "CareBot stopped"
        else
            echo "CareBot is not running"
        fi
        ;;
    restart)
        `$0 stop
        sleep 2
        `$0 start
        ;;
    status)
        if [ -f "`$PID_FILE" ]; then
            PID=`$(cat `$PID_FILE)
            if ps -p `$PID > /dev/null; then
                echo "CareBot is running (PID: `$PID)"
            else
                echo "CareBot is not running (stale PID file)"
                rm `$PID_FILE
            fi
        else
            echo "CareBot is not running"
        fi
        ;;
    *)
        echo "Usage: `$0 {start|stop|restart|status}"
        exit 1
        ;;
esac
"@
    
    $serviceScript | Out-File -FilePath "$tempDir\carebot-service.sh" -Encoding UTF8
    
    # Create requirements.txt if missing
    if (-not (Test-Path "$tempDir\requirements.txt")) {
        @"
Flask>=2.2.3
aiosqlite>=0.19.0
"@ | Out-File -FilePath "$tempDir\requirements.txt" -Encoding UTF8
    }
    
    # Create archive
    Write-Host "Creating archive..." -ForegroundColor Yellow
    $archiveName = "carebot-deploy.zip"
    if (Test-Path $archiveName) {
        Remove-Item $archiveName
    }
    
    # Use PowerShell 5 compatible compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($tempDir, $archiveName)
    
    # Copy to remote server
    Write-Host "Copying files to remote server..." -ForegroundColor Yellow
    
    # Ensure remote directory exists
    ssh "$RemoteUser@$RemoteHost" "mkdir -p /home/ubuntu/carebot/logs"
    
    # Copy archive
    scp $archiveName "$RemoteUser@$RemoteHost":/home/ubuntu/
    
    # Extract and setup on remote server
    Write-Host "Setting up application on remote server..." -ForegroundColor Yellow
    
    ssh "$RemoteUser@$RemoteHost" "cd /home/ubuntu && unzip -o $archiveName -d carebot_temp"
    ssh "$RemoteUser@$RemoteHost" "cp -r carebot_temp/* carebot/ 2>/dev/null || mkdir -p carebot && cp -r carebot_temp/* carebot/"
    ssh "$RemoteUser@$RemoteHost" "rm -rf carebot_temp $archiveName"
    ssh "$RemoteUser@$RemoteHost" "cd carebot && chmod +x carebot-service.sh"
    ssh "$RemoteUser@$RemoteHost" "cd carebot && ./carebot-service.sh stop || true"
    ssh "$RemoteUser@$RemoteHost" "cd carebot && ./carebot-service.sh start"
    
    # Cleanup local files
    Remove-Item $tempDir -Recurse -Force
    Remove-Item $archiveName
    
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host "Application should be available at http://$RemoteHost:5555" -ForegroundColor Cyan
    
    # Test connection
    Write-Host "Testing connection..." -ForegroundColor Yellow
    Start-Sleep 5
    
    try {
        $response = Invoke-WebRequest -Uri "http://$RemoteHost:5555/health" -TimeoutSec 10 -ErrorAction Stop
        Write-Host "Health check passed!" -ForegroundColor Green
    }
    catch {
        Write-Host "Health check failed - checking service status..." -ForegroundColor Red
        ssh "$RemoteUser@$RemoteHost" "cd /home/ubuntu/carebot && ./carebot-service.sh status"
        Write-Host "Check logs with: ssh $RemoteUser@$RemoteHost 'tail -f /home/ubuntu/carebot/logs/app.log'" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    
    # Cleanup on failure
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path $archiveName) {
        Remove-Item $archiveName -ErrorAction SilentlyContinue
    }
    
    exit 1
}

Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  Check status: ssh $RemoteUser@$RemoteHost 'cd /home/ubuntu/carebot && ./carebot-service.sh status'" -ForegroundColor White
Write-Host "  View logs: ssh $RemoteUser@$RemoteHost 'tail -f /home/ubuntu/carebot/logs/app.log'" -ForegroundColor White
Write-Host "  Restart: ssh $RemoteUser@$RemoteHost 'cd /home/ubuntu/carebot && ./carebot-service.sh restart'" -ForegroundColor White
Write-Host "  Stop: ssh $RemoteUser@$RemoteHost 'cd /home/ubuntu/carebot && ./carebot-service.sh stop'" -ForegroundColor White
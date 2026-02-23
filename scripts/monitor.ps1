# CareBot Monitoring and Logs Script

param(
    [string]$RemoteHost = "192.168.1.125",
    [string]$RemoteUser = "ubuntu",
    [switch]$Logs,
    [switch]$Status,
    [switch]$Restart,
    [switch]$Stop,
    [switch]$Start,
    [int]$LogLines = 50
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host "📊 CareBot Monitoring Tool" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\monitor.ps1 -Status        # Show container status"
    Write-Host "  .\monitor.ps1 -Logs          # Show application logs"
    Write-Host "  .\monitor.ps1 -Restart       # Restart the application"
    Write-Host "  .\monitor.ps1 -Stop          # Stop the application"
    Write-Host "  .\monitor.ps1 -Start         # Start the application"
    Write-Host ""
    Write-Host "Parameters:" -ForegroundColor Yellow
    Write-Host "  -LogLines     : Number of log lines to show (default: 50)"
}

if (-not $Logs -and -not $Status -and -not $Restart -and -not $Stop -and -not $Start) {
    Show-Help
    exit 0
}

$containerName = "carebot-app"
$projectPath = "/home/ubuntu/carebot"

if ($Status) {
    Write-Host "📊 Checking CareBot status..." -ForegroundColor Yellow
    
    try {
        $status = ssh "$RemoteUser@$RemoteHost" "docker ps -a | grep $containerName"
        Write-Host "Container Status:" -ForegroundColor Green
        Write-Host $status -ForegroundColor White
        
        # Check if container is running
        $running = ssh "$RemoteUser@$RemoteHost" "docker ps | grep $containerName | wc -l"
        if ($running -eq "1") {
            Write-Host "✅ Container is running" -ForegroundColor Green
            
            # Check health
            try {
                $response = Invoke-WebRequest -Uri "http://$RemoteHost:5555/health" -TimeoutSec 5 -ErrorAction Stop
                Write-Host "✅ Application is responding" -ForegroundColor Green
            }
            catch {
                Write-Host "⚠️  Application is not responding" -ForegroundColor Red
            }
        } else {
            Write-Host "❌ Container is not running" -ForegroundColor Red
        }
        
        # Show resource usage
        $stats = ssh "$RemoteUser@$RemoteHost" "docker stats $containerName --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}'"
        Write-Host "`nResource Usage:" -ForegroundColor Green
        Write-Host $stats -ForegroundColor White
        
    }
    catch {
        Write-Host "❌ Failed to check status: $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($Logs) {
    Write-Host "📋 Fetching application logs (last $LogLines lines)..." -ForegroundColor Yellow
    
    try {
        $logs = ssh "$RemoteUser@$RemoteHost" "docker logs $containerName --tail $LogLines"
        Write-Host "Application Logs:" -ForegroundColor Green
        Write-Host $logs -ForegroundColor White
    }
    catch {
        Write-Host "❌ Failed to fetch logs: $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($Restart) {
    Write-Host "🔄 Restarting CareBot application..." -ForegroundColor Yellow
    
    try {
        ssh "$RemoteUser@$RemoteHost" "cd $projectPath && docker-compose restart"
        Write-Host "✅ Application restarted successfully" -ForegroundColor Green
        
        # Wait a moment and check status
        Start-Sleep 5
        $running = ssh "$RemoteUser@$RemoteHost" "docker ps | grep $containerName | wc -l"
        if ($running -eq "1") {
            Write-Host "✅ Container is running after restart" -ForegroundColor Green
        } else {
            Write-Host "❌ Container failed to start after restart" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Failed to restart: $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($Stop) {
    Write-Host "🛑 Stopping CareBot application..." -ForegroundColor Yellow
    
    try {
        ssh "$RemoteUser@$RemoteHost" "cd $projectPath && docker-compose down"
        Write-Host "✅ Application stopped successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Failed to stop: $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($Start) {
    Write-Host "🚀 Starting CareBot application..." -ForegroundColor Yellow
    
    try {
        ssh "$RemoteUser@$RemoteHost" "cd $projectPath && docker-compose up -d"
        Write-Host "✅ Application started successfully" -ForegroundColor Green
        
        # Wait a moment and check status
        Start-Sleep 5
        $running = ssh "$RemoteUser@$RemoteHost" "docker ps | grep $containerName | wc -l"
        if ($running -eq "1") {
            Write-Host "✅ Container is running" -ForegroundColor Green
        } else {
            Write-Host "❌ Container failed to start" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Failed to start: $($_.Exception.Message)" -ForegroundColor Red
    }
}
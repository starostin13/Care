# Local Docker Test Script
# Test the Docker build and run locally before deploying

param(
    [switch]$Build,
    [switch]$Run,
    [switch]$Stop,
    [switch]$Logs,
    [switch]$Test
)

$ErrorActionPreference = "Stop"

$imageName = "carebot"
$containerName = "carebot-local"

function Show-Help {
    Write-Host "CareBot Local Test Tool" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\test-local.ps1 -Build       # Build Docker image"
    Write-Host "  .\test-local.ps1 -Run         # Run container locally"
    Write-Host "  .\test-local.ps1 -Stop        # Stop local container"
    Write-Host "  .\test-local.ps1 -Logs        # Show container logs"
    Write-Host "  .\test-local.ps1 -Test        # Test health endpoint"
}

if (-not $Build -and -not $Run -and -not $Stop -and -not $Logs -and -not $Test) {
    Show-Help
    exit 0
}

if ($Build) {
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    docker build -t $imageName .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Image built successfully" -ForegroundColor Green
    } else {
        Write-Host "Build failed" -ForegroundColor Red
        exit 1
    }
}

if ($Run) {
    Write-Host "Starting local container..." -ForegroundColor Yellow
    
    # Stop existing container if running
    docker stop $containerName 2>$null
    docker rm $containerName 2>$null
    
    # Create local data directory
    if (-not (Test-Path ".\data")) {
        New-Item -ItemType Directory -Path ".\data"
    }
    
    # Run container
    docker run -d `
        --name $containerName `
        -p 5555:5555 `
        -v "${PWD}\data:/app/data" `
        -e DATABASE_PATH=/app/data/game_database.db `
        $imageName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Container started successfully" -ForegroundColor Green
        Write-Host "Application available at http://localhost:5555" -ForegroundColor Cyan
        
        # Wait a moment and test
        Start-Sleep 3
        & $PSCommandPath -Test
    } else {
        Write-Host "Failed to start container" -ForegroundColor Red
        exit 1
    }
}

if ($Stop) {
    Write-Host "Stopping local container..." -ForegroundColor Yellow
    docker stop $containerName
    docker rm $containerName
    Write-Host "Container stopped" -ForegroundColor Green
}

if ($Logs) {
    Write-Host "Container logs:" -ForegroundColor Yellow
    docker logs $containerName
}

if ($Test) {
    Write-Host "Testing health endpoint..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5555/health" -TimeoutSec 10
        $health = $response.Content | ConvertFrom-Json
        
        Write-Host "Health check passed!" -ForegroundColor Green
        Write-Host "Status: $($health.status)" -ForegroundColor White
        Write-Host "Database: $($health.database)" -ForegroundColor White
        Write-Host "Timestamp: $($health.timestamp)" -ForegroundColor White
    }
    catch {
        Write-Host "Health check failed: $($_.Exception.Message)" -ForegroundColor Red
        
        # Show logs if health check fails
        Write-Host "Recent logs:" -ForegroundColor Yellow
        docker logs $containerName --tail 20
    }
}
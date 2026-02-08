# CareBot WSL2 Deployment Script
# Использует Docker в WSL2 для локальной сборки и деплоя на production

param(
    [string]$Action = "help",
    [string]$Tag = "latest",
    [switch]$NoCache,
    [switch]$Force,
    [switch]$SkipHealthCheck
)

# Configuration
$IMAGE_NAME = "carebot"
$CONTAINER_NAME = "carebot_production"
$SERVER_HOST = "ubuntu@192.168.1.125"
$PRODUCTION_PATH = "/home/ubuntu/carebot-production"
$HEALTH_URL = "http://192.168.1.125:5555/health"
$LOCAL_HEALTH_URL = "http://localhost:5556/health"
$LOCAL_ENV_FILE = ".env"

# WSL2 Configuration
$WSL_DISTRO = "Ubuntu"
$PROJECT_PATH_WIN = Get-Location
$PROJECT_PATH_WSL = $PROJECT_PATH_WIN.Path -replace '\\', '/' -replace 'C:', '/mnt/c' -replace 'c:', '/mnt/c'

# Timeouts (seconds)
$TIMEOUT_BUILD_SEC = 2400
$TIMEOUT_SAVE_SEC = 900
$TIMEOUT_TRANSFER_SEC = 1200
$TIMEOUT_LOAD_SEC = 900
$TIMEOUT_RESTART_SEC = 300

# Colors
function Write-Success($text) { Write-Host "SUCCESS: $text" -ForegroundColor Green }
function Write-Error($text) { Write-Host "ERROR: $text" -ForegroundColor Red }
function Write-Info($text) { Write-Host "INFO: $text" -ForegroundColor Cyan }
function Write-Warning($text) { Write-Host "WARNING: $text" -ForegroundColor Yellow }

# Run external command with spinner and optional timeout
function Invoke-ExternalWithProgress {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$Activity,
        [int]$TimeoutSec = 0,
        [int]$ProgressIntervalMs = 250
    )

    $job = Start-Job -ScriptBlock {
        param($exe, $args)
        $output = & $exe @args 2>&1
        $exitCode = $LASTEXITCODE
        [pscustomobject]@{ Output = $output; ExitCode = $exitCode }
    } -ArgumentList $FilePath, $Arguments

    $spinner = @('|', '/', '-', '\\')
    $i = 0
    $start = Get-Date

    while ($job.State -eq 'Running') {
        $elapsed = (Get-Date) - $start
        $status = "{0} Elapsed {1:hh\:mm\:ss}" -f $spinner[$i % $spinner.Count], $elapsed
        $percent = 0
        if ($TimeoutSec -gt 0) {
            $percent = [math]::Min(99, ($elapsed.TotalSeconds / $TimeoutSec) * 100)
        }

        Write-Progress -Activity $Activity -Status $status -PercentComplete $percent
        Start-Sleep -Milliseconds $ProgressIntervalMs

        if ($TimeoutSec -gt 0 -and $elapsed.TotalSeconds -ge $TimeoutSec) {
            Stop-Job $job | Out-Null
            Remove-Job $job | Out-Null
            Write-Progress -Activity $Activity -Completed
            Write-Error "Timeout after ${TimeoutSec}s: $FilePath $($Arguments -join ' ')"
            return $false
        }

        $i++
    }

    $result = Receive-Job $job
    Remove-Job $job | Out-Null
    Write-Progress -Activity $Activity -Completed

    if ($result.Output) {
        $result.Output | ForEach-Object { Write-Host $_ }
    }

    if ($result.ExitCode -ne 0) {
        Write-Error "Command failed with exit code $($result.ExitCode): $FilePath"
        return $false
    }

    return $true
}

# Check WSL2
function Test-WSL2 {
    Write-Info "Checking WSL2..."
    
    try {
        $wslVersion = wsl --status 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "WSL not installed or not running"
            Write-Info "Install WSL2: wsl --install"
            return $false
        }
        
        Write-Success "WSL2 is available"
        return $true
    }
    catch {
        Write-Error "Failed to check WSL2: $($_.Exception.Message)"
        return $false
    }
}

# Check Docker in WSL2
function Test-DockerWSL {
    Write-Info "Checking Docker in WSL2..."
    
    $result = wsl -d $WSL_DISTRO -e bash -c "docker --version" 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker not installed in WSL2"
        Write-Info "Install Docker in WSL2:"
        Write-Host "  wsl -d $WSL_DISTRO"
        Write-Host "  sudo apt update && sudo apt install -y docker.io"
        Write-Host "  sudo service docker start"
        return $false
    }
    
    Write-Success "Docker is available: $result"

    # Check if Docker daemon is running and accessible without sudo
    $dockerInfo = wsl -d $WSL_DISTRO -e bash -c "docker info" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker daemon is not running or permission denied"
        Write-Info "If needed, start it manually: wsl -d $WSL_DISTRO -e bash -lc 'sudo service docker start'"
        Write-Info "If permission denied, add user to docker group and restart WSL"
        return $false
    }
    
    return $true
}

# Production safety check
function Test-ProductionSafety {
    Write-Info "Running production safety check..."
    
    try {
        python scripts\check-production-safety.py
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Success "Production safety check passed"
            return $true
        } else {
            Write-Error "Production safety check FAILED!"
            Write-Warning "Fix security issues before building image"
            return $false
        }
    } catch {
        Write-Error "Failed to run safety check: $($_.Exception.Message)"
        return $false
    }
}

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

# Build Docker image in WSL2
function Build-Image {
    Write-Info "Building Docker image in WSL2..."
    
    if (-not (Test-WSL2)) { return $false }
    if (-not (Test-DockerWSL)) { return $false }
    if (-not (Test-ProductionSafety)) { return $false }
    
    $buildArgs = ""
    if ($NoCache) {
        $buildArgs = "--no-cache"
    }
    
    Write-Info "Building image: ${IMAGE_NAME}:${Tag}"
    Write-Info "Project path (WSL): $PROJECT_PATH_WSL"
    
    $buildCmd = "cd '$PROJECT_PATH_WSL' && docker build $buildArgs -t ${IMAGE_NAME}:${Tag} -f Dockerfile.production ."
    
    Write-Info "Executing: $buildCmd"
    
    $ok = Invoke-ExternalWithProgress -FilePath "wsl" -Arguments @("-d", $WSL_DISTRO, "-e", "bash", "-c", $buildCmd) -Activity "Building Docker image" -TimeoutSec $TIMEOUT_BUILD_SEC
    if (-not $ok) { return $false }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Image built successfully: ${IMAGE_NAME}:${Tag}"
        return $true
    } else {
        Write-Error "Failed to build image"
        return $false
    }
}

# Inspect image contents
function Show-ImageInspect {
    Write-Info "Inspecting image contents..."
    
    if (-not (Test-DockerWSL)) { return }
    
    Write-Info "Image details:"
    wsl -d $WSL_DISTRO -e bash -c "docker images ${IMAGE_NAME}:${Tag}"
    
    Write-Info "`nListing files in image /app/CareBot/:"
    wsl -d $WSL_DISTRO -e bash -c "docker run --rm ${IMAGE_NAME}:${Tag} ls -lah /app/CareBot/"
    
    Write-Info "`nChecking key files:"
    $keyFiles = @(
        "/app/run_hybrid.py",
        "/app/CareBot/handlers.py",
        "/app/CareBot/mission_helper.py",
        "/app/CareBot/sqllite_helper.py",
        "/app/CareBot/config.py"
    )
    
    foreach ($file in $keyFiles) {
        $exists = wsl -d $WSL_DISTRO -e bash -c "docker run --rm ${IMAGE_NAME}:${Tag} test -f $file && echo 'EXISTS' || echo 'MISSING'"
        if ($exists -match "EXISTS") {
            Write-Success "$file - EXISTS"
        } else {
            Write-Error "$file - MISSING"
        }
    }
    
    Write-Info "`nEnvironment variables:"
    wsl -d $WSL_DISTRO -e bash -c "docker inspect ${IMAGE_NAME}:${Tag} --format='{{.Config.Env}}'"
    
    Write-Info "`nExposed ports:"
    wsl -d $WSL_DISTRO -e bash -c "docker inspect ${IMAGE_NAME}:${Tag} --format='{{.Config.ExposedPorts}}'"
    
    Write-Info "`nImage layers:"
    wsl -d $WSL_DISTRO -e bash -c "docker history ${IMAGE_NAME}:${Tag}"
}

# Test image locally
function Test-ImageLocally {
    Write-Info "Testing image locally..."
    
    if (-not (Test-DockerWSL)) { return $false }
    if (-not (Test-Token)) { return $false }
    
    # Stop existing test container
    Write-Info "Stopping existing test container..."
    wsl -d $WSL_DISTRO -e bash -c "docker stop carebot_test 2>/dev/null || true"
    wsl -d $WSL_DISTRO -e bash -c "docker rm carebot_test 2>/dev/null || true"
    
    # Get token
    $token = Get-Content $LOCAL_ENV_FILE | Where-Object { $_ -match "TELEGRAM_BOT_TOKEN=" } | ForEach-Object { $_.Split('=')[1] }
    
    # Create test data directory
    $testDataPath = Join-Path $PROJECT_PATH_WIN "test-data"
    if (-not (Test-Path $testDataPath)) {
        New-Item -ItemType Directory -Path $testDataPath | Out-Null
    }
    
    $testDataPathWSL = $testDataPath -replace '\\', '/' -replace 'C:', '/mnt/c' -replace 'c:', '/mnt/c'
    
    Write-Info "Starting test container on port 5556..."
    Write-Info "Data directory: $testDataPath"
    
    $runCmd = "cd '$PROJECT_PATH_WSL' && docker run -d --name carebot_test " +
              "-p 5556:5555 " +
              "-v '${testDataPathWSL}:/app/data' " +
              "-e TELEGRAM_BOT_TOKEN='$token' " +
              "-e DATABASE_PATH='/app/data/game_database.db' " +
              "-e SERVER_HOST='0.0.0.0' " +
              "-e SERVER_PORT='5555' " +
              "${IMAGE_NAME}:${Tag}"
    
    wsl -d $WSL_DISTRO -e bash -c $runCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start test container"
        return $false
    }
    
    Write-Info "Waiting for container to start..."
    Start-Sleep -Seconds 10
    
    Write-Info "Container logs:"
    wsl -d $WSL_DISTRO -e bash -c "docker logs carebot_test --tail=20"
    
    Write-Info "`nTesting health endpoint..."
    try {
        $response = Invoke-WebRequest -Uri $LOCAL_HEALTH_URL -Method GET -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Success "Health check passed!"
            Write-Info "Response: $($response.Content)"
            Write-Info "`nTest container is running: $LOCAL_HEALTH_URL"
            Write-Info "To stop: .\scripts\wsl2-deploy.ps1 stop-test"
            return $true
        }
    }
    catch {
        Write-Error "Health check failed: $($_.Exception.Message)"
        Write-Info "Check logs: wsl -d $WSL_DISTRO -e bash -c 'docker logs carebot_test'"
        return $false
    }
}

# Stop test container
function Stop-TestContainer {
    Write-Info "Stopping test container..."
    wsl -d $WSL_DISTRO -e bash -c "docker stop carebot_test 2>/dev/null || true"
    wsl -d $WSL_DISTRO -e bash -c "docker rm carebot_test 2>/dev/null || true"
    Write-Success "Test container stopped"
}

# Save image to tar
function Save-Image {
    param([string]$OutputPath)
    
    Write-Info "Saving image to tar file..."
    
    $outputPathWSL = $OutputPath -replace '\\', '/' -replace 'C:', '/mnt/c' -replace 'c:', '/mnt/c'
    
    Write-Info "Saving ${IMAGE_NAME}:${Tag} to $OutputPath..."
    $ok = Invoke-ExternalWithProgress -FilePath "wsl" -Arguments @("-d", $WSL_DISTRO, "-e", "bash", "-c", "docker save ${IMAGE_NAME}:${Tag} -o '$outputPathWSL'") -Activity "Saving Docker image" -TimeoutSec $TIMEOUT_SAVE_SEC
    if (-not $ok) { return $false }
    
    if ($LASTEXITCODE -eq 0) {
        $fileSize = (Get-Item $OutputPath).Length / 1MB
        Write-Success "Image saved: $OutputPath ($([math]::Round($fileSize, 2)) MB)"
        return $true
    } else {
        Write-Error "Failed to save image"
        return $false
    }
}

# Transfer image to production
function Transfer-Image {
    Write-Info "Transferring image to production..."
    
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $tarFile = "carebot-${timestamp}.tar"
    $tarPath = Join-Path $env:TEMP $tarFile
    
    # Save image
    if (-not (Save-Image -OutputPath $tarPath)) { return $false }
    
    # Create production directory
    Write-Info "Preparing production directory..."
    ssh $SERVER_HOST "mkdir -p $PRODUCTION_PATH"
    
    # Transfer tar file
    Write-Info "Transferring tar file to production (this may take a while)..."
    $ok = Invoke-ExternalWithProgress -FilePath "scp" -Arguments @($tarPath, "${SERVER_HOST}:${PRODUCTION_PATH}/${tarFile}") -Activity "Transferring image to production" -TimeoutSec $TIMEOUT_TRANSFER_SEC
    if (-not $ok) {
        Remove-Item $tarPath -Force
        return $false
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to transfer image"
        Remove-Item $tarPath -Force
        return $false
    }
    
    Write-Success "Image transferred"
    
    # Load image on production
    Write-Info "Loading image on production server..."
    $ok = Invoke-ExternalWithProgress -FilePath "ssh" -Arguments @($SERVER_HOST, "cd $PRODUCTION_PATH && docker load -i $tarFile") -Activity "Loading image on production" -TimeoutSec $TIMEOUT_LOAD_SEC
    if (-not $ok) { return $false }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to load image on production"
        return $false
    }
    
    Write-Success "Image loaded on production"
    
    # Cleanup
    Write-Info "Cleaning up temporary files..."
    ssh $SERVER_HOST "rm -f ${PRODUCTION_PATH}/${tarFile}"
    Remove-Item $tarPath -Force
    
    Write-Success "Image transfer completed"
    return $true
}

# Deploy to production
function Deploy-Production {
    Write-Info "Deploying to production..."
    
    # Create backup
    if (-not $Force) {
        $answer = Read-Host "Create backup before deployment? (Y/n)"
        if ($answer -ne "n" -and $answer -ne "N") {
            Create-Backup
        }
    } else {
        Create-Backup
    }
    
    # Sync essential files
    Sync-ProductionFiles
    
    # Transfer image
    if (-not (Transfer-Image)) { return $false }

    # Update image tag in production .env
    Set-ProductionImageTag -ImageTag $Tag
    
    # Restart production container with new image
    Write-Info "Restarting production container..."
    $ok = Invoke-ExternalWithProgress -FilePath "ssh" -Arguments @($SERVER_HOST, "cd $PRODUCTION_PATH && docker compose -f docker-compose.production.yml down") -Activity "Stopping production container" -TimeoutSec $TIMEOUT_RESTART_SEC
    if (-not $ok) { return $false }

    $ok = Invoke-ExternalWithProgress -FilePath "ssh" -Arguments @($SERVER_HOST, "cd $PRODUCTION_PATH && docker compose -f docker-compose.production.yml up -d") -Activity "Starting production container" -TimeoutSec $TIMEOUT_RESTART_SEC
    if (-not $ok) { return $false }
    
    if (-not $SkipHealthCheck) {
        Start-Sleep -Seconds 10
        Test-ProductionHealth
    }
    
    Write-Success "Deployment completed!"
}

# Sync production files (docker-compose, .env, migrations)
function Sync-ProductionFiles {
    Write-Info "Syncing production files..."
    
    # Sync docker-compose
    scp "docker-compose.production.yml" "${SERVER_HOST}:${PRODUCTION_PATH}/"
    
    # Sync .env
    scp ".env" "${SERVER_HOST}:${PRODUCTION_PATH}/"
    
    # Sync migrations
    ssh $SERVER_HOST "mkdir -p $PRODUCTION_PATH/migrations"
    $migrationFiles = Get-ChildItem -Path "CareBot/CareBot/migrations/" -File -ErrorAction SilentlyContinue
    foreach ($migration in $migrationFiles) {
        scp "CareBot/CareBot/migrations/$($migration.Name)" "${SERVER_HOST}:${PRODUCTION_PATH}/migrations/"
    }
    
    Write-Success "Files synced"
}

# Ensure production uses the intended image tag
function Set-ProductionImageTag {
    param([string]$ImageTag)

    Write-Info "Setting production image tag to $ImageTag..."
    ssh $SERVER_HOST "mkdir -p $PRODUCTION_PATH"
    ssh $SERVER_HOST "cd $PRODUCTION_PATH && if [ -f .env ]; then sed -i '/^CAREBOT_IMAGE_TAG=/d' .env; fi; echo \"CAREBOT_IMAGE_TAG=$ImageTag\" >> .env"
    Write-Success "Production image tag set"
}

# Test production health
function Test-ProductionHealth {
    Write-Info "Checking production health..."
    
    Start-Sleep -Seconds 5
    
    try {
        $response = Invoke-WebRequest -Uri $HEALTH_URL -Method GET -TimeoutSec 10
        
        if ($response.StatusCode -eq 200) {
            $healthData = $response.Content | ConvertFrom-Json
            Write-Success "Production is healthy! Status: $($healthData.status)"
            return $true
        }
    }
    catch {
        Write-Warning "Health check failed: $($_.Exception.Message)"
        return $false
    }
    
    return $false
}

# Create backup
function Create-Backup {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = "carebot-backup-$timestamp"
    
    Write-Info "Creating backup..."
    ssh $SERVER_HOST "cd /home/ubuntu && cp -r carebot-production $backupPath"
    
    Write-Success "Backup created: $backupPath"
}

# List images
function Show-Images {
    Write-Info "Docker images in WSL2:"
    wsl -d $WSL_DISTRO -e bash -c "docker images | grep -E '(REPOSITORY|carebot)'"
}

# Cleanup old images
function Clean-Images {
    Write-Info "Cleaning up old Docker images..."
    
    # Remove dangling images
    wsl -d $WSL_DISTRO -e bash -c "docker image prune -f"
    
    # Remove old carebot images (keep latest)
    wsl -d $WSL_DISTRO -e bash -c "docker images ${IMAGE_NAME} --format '{{.Tag}}' | grep -v 'latest' | xargs -r -I {} docker rmi ${IMAGE_NAME}:{}"
    
    Write-Success "Cleanup completed"
}

# Show production status
function Show-ProductionStatus {
    Write-Info "Production status:"
    ssh $SERVER_HOST "cd $PRODUCTION_PATH && docker compose -f docker-compose.production.yml ps"
    
    Write-Info "`nTesting health endpoint..."
    Test-ProductionHealth
}

# Show production logs
function Show-ProductionLogs {
    Write-Info "Production logs (last 50 lines):"
    ssh $SERVER_HOST "cd $PRODUCTION_PATH && docker compose -f docker-compose.production.yml logs --tail=50"
}

# Restart production
function Restart-Production {
    Write-Info "Restarting production..."
    ssh $SERVER_HOST "cd $PRODUCTION_PATH && docker compose -f docker-compose.production.yml restart"
    
    Start-Sleep -Seconds 10
    Test-ProductionHealth
}

# Sync and apply migrations
function Sync-Migrations {
    Write-Info "Syncing migrations..."
    
    ssh $SERVER_HOST "mkdir -p $PRODUCTION_PATH/migrations"
    
    $migrationFiles = Get-ChildItem -Path "CareBot/CareBot/migrations/" -File -ErrorAction SilentlyContinue
    $migrationCount = 0
    
    foreach ($migration in $migrationFiles) {
        Write-Host "  Copying migration: $($migration.Name)..."
        scp "CareBot/CareBot/migrations/$($migration.Name)" "${SERVER_HOST}:${PRODUCTION_PATH}/migrations/$($migration.Name)"
        $migrationCount++
    }
    
    Write-Success "Synced $migrationCount migration files"
}

function Apply-Migrations {
    Write-Info "Applying migrations on production..."
    ssh $SERVER_HOST "cd $PRODUCTION_PATH && docker exec $CONTAINER_NAME python /app/CareBot/migrate_db.py"
    Write-Success "Migrations applied"
}

function Show-MigrationStatus {
    Write-Info "Migration status on production:"
    ssh $SERVER_HOST "cd $PRODUCTION_PATH && docker exec $CONTAINER_NAME python /app/CareBot/migrate_db.py --status"
}

# Full workflow
function Run-FullWorkflow {
    Write-Info "Running full deployment workflow..."
    
    # Build
    if (-not (Build-Image)) {
        Write-Error "Build failed, aborting"
        return
    }
    
    # Inspect
    Show-ImageInspect
    
    # Test locally
    $answer = Read-Host "`nTest image locally before deploying? (Y/n)"
    if ($answer -ne "n" -and $answer -ne "N") {
        if (Test-ImageLocally) {
            $answer = Read-Host "`nContinue with deployment? (Y/n)"
            if ($answer -eq "n" -or $answer -eq "N") {
                Write-Warning "Deployment cancelled"
                Stop-TestContainer
                return
            }
            Stop-TestContainer
        } else {
            Write-Error "Local test failed, aborting deployment"
            return
        }
    }
    
    # Deploy
    Deploy-Production
    
    Write-Success "Full workflow completed!"
}

# Main script logic
switch ($Action.ToLower()) {
    "build" {
        Build-Image
    }
    "inspect" {
        Show-ImageInspect
    }
    "test" {
        Test-ImageLocally
    }
    "stop-test" {
        Stop-TestContainer
    }
    "save" {
        $tarPath = Join-Path (Get-Location) "carebot-${Tag}.tar"
        Save-Image -OutputPath $tarPath
    }
    "deploy" {
        Deploy-Production
    }
    "full" {
        Run-FullWorkflow
    }
    "images" {
        Show-Images
    }
    "cleanup" {
        Clean-Images
    }
    "status" {
        Show-ProductionStatus
    }
    "logs" {
        Show-ProductionLogs
    }
    "restart" {
        Restart-Production
    }
    "backup" {
        Create-Backup
    }
    "migrations" {
        Sync-Migrations
    }
    "apply-migrations" {
        Apply-Migrations
    }
    "migration-status" {
        Show-MigrationStatus
    }
    "check-wsl" {
        Test-WSL2
        Test-DockerWSL
    }
    "safety-check" {
        Test-ProductionSafety | Out-Null
    }
    default {
        Write-Host ""
        Write-Host "🐳 CareBot WSL2 Deployment Script" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Usage: .\scripts\wsl2-deploy.ps1 [action] [options]"
        Write-Host ""
        Write-Host "🏗️  Build & Test:" -ForegroundColor Cyan
        Write-Host "  build            - Build Docker image in WSL2"
        Write-Host "  inspect          - Inspect image contents"
        Write-Host "  test             - Test image locally on port 5556"
        Write-Host "  stop-test        - Stop local test container"
        Write-Host "  save             - Save image to tar file"
        Write-Host ""
        Write-Host "🚀 Deployment:" -ForegroundColor Cyan
        Write-Host "  deploy           - Deploy image to production"
        Write-Host "  full             - Full workflow (build → inspect → test → deploy)"
        Write-Host ""
        Write-Host "📊 Management:" -ForegroundColor Cyan
        Write-Host "  status           - Show production status"
        Write-Host "  logs             - Show production logs"
        Write-Host "  restart          - Restart production"
        Write-Host "  backup           - Create backup"
        Write-Host ""
        Write-Host "🔄 Migrations:" -ForegroundColor Cyan
        Write-Host "  migrations       - Sync migration files"
        Write-Host "  apply-migrations - Apply migrations"
        Write-Host "  migration-status - Check migration status"
        Write-Host ""
        Write-Host "🔧 Utilities:" -ForegroundColor Cyan
        Write-Host "  images           - List Docker images"
        Write-Host "  cleanup          - Clean up old images"
        Write-Host "  check-wsl        - Check WSL2 and Docker setup"
        Write-Host "  safety-check     - Run production safety check"
        Write-Host ""
        Write-Host "⚙️  Options:" -ForegroundColor Cyan
        Write-Host "  -Tag <tag>       - Image tag (default: latest)"
        Write-Host "  -NoCache         - Build without cache"
        Write-Host "  -Force           - Skip confirmations"
        Write-Host "  -SkipHealthCheck - Skip health check after deploy"
        Write-Host ""
        Write-Host "📚 Examples:" -ForegroundColor Cyan
        Write-Host "  .\scripts\wsl2-deploy.ps1 build"
        Write-Host "  .\scripts\wsl2-deploy.ps1 full"
        Write-Host "  .\scripts\wsl2-deploy.ps1 build -Tag v1.2.3 -NoCache"
        Write-Host "  .\scripts\wsl2-deploy.ps1 test"
        Write-Host "  .\scripts\wsl2-deploy.ps1 deploy -Force"
        Write-Host ""
        Write-Host "📖 Documentation: WSL2_DEPLOYMENT.md" -ForegroundColor Green
        Write-Host ""
    }
}

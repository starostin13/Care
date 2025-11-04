# Simple PowerShell wrapper for CareBot management
# Version: 1.0 - Backup System Integration

param([string]$Action = "help")

$SERVER = "192.168.0.125"
$USER = "ubuntu" 
$PATH = "/home/ubuntu/carebot"

switch ($Action) {
    "backup" {
        Write-Host "Creating database backup..." -ForegroundColor Cyan
        ssh ${USER}@${SERVER} "cd ${PATH} && ./scripts/backup-database.sh"
    }
    "restore" {
        Write-Host "Restoring from latest backup..." -ForegroundColor Cyan
        ssh ${USER}@${SERVER} "cd ${PATH} && ./scripts/restore-database.sh"
    }
    "status" {
        Write-Host "Checking services..." -ForegroundColor Cyan
        ssh ${USER}@${SERVER} "cd ${PATH} && docker-compose ps"
    }
    "logs" {
        Write-Host "Showing logs..." -ForegroundColor Cyan
        ssh ${USER}@${SERVER} "cd ${PATH} && docker-compose logs carebot"
    }
    "restart" {
        Write-Host "Restarting services..." -ForegroundColor Cyan
        ssh ${USER}@${SERVER} "cd ${PATH} && docker-compose restart"
    }
    default {
        Write-Host "CareBot Management Script" -ForegroundColor Yellow
        Write-Host "Usage: .\manage-carebot.ps1 [action]" -ForegroundColor White
        Write-Host ""
        Write-Host "Actions:" -ForegroundColor Cyan
        Write-Host "  backup  - Create database backup" -ForegroundColor White
        Write-Host "  restore - Restore from latest backup" -ForegroundColor White
        Write-Host "  status  - Check service status" -ForegroundColor White
        Write-Host "  logs    - View application logs" -ForegroundColor White
        Write-Host "  restart - Restart all services" -ForegroundColor White
    }
}
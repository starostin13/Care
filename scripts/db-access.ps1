# Database Remote Access Script
# This script helps you connect to the CareBot database on the remote server

param(
    [string]$RemoteHost = "192.168.1.125",
    [string]$RemoteUser = "ubuntu",
    [string]$LocalPort = "5432",
    [switch]$CopyDatabase,
    [switch]$OpenTunnel,
    [switch]$RunQuery,
    [string]$Query
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host "🔧 CareBot Database Access Tool" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\db-access.ps1 -CopyDatabase     # Copy database to local machine"
    Write-Host "  .\db-access.ps1 -OpenTunnel       # Open SSH tunnel for database access"
    Write-Host "  .\db-access.ps1 -RunQuery 'SELECT * FROM mission_stack LIMIT 5'"
    Write-Host ""
    Write-Host "Parameters:" -ForegroundColor Yellow
    Write-Host "  -RemoteHost   : Remote server IP (default: 192.168.1.125)"
    Write-Host "  -RemoteUser   : Remote username (default: ubuntu)"
    Write-Host "  -LocalPort    : Local port for tunnel (default: 5432)"
}

if (-not $CopyDatabase -and -not $OpenTunnel -and -not $RunQuery) {
    Show-Help
    exit 0
}

if ($CopyDatabase) {
    Write-Host "📥 Copying database from remote server..." -ForegroundColor Yellow
    
    # Create local data directory if it doesn't exist
    if (-not (Test-Path ".\data")) {
        New-Item -ItemType Directory -Path ".\data"
    }
    
    # Copy database file
    try {
        scp "$RemoteUser@$RemoteHost":/home/ubuntu/carebot/data/game_database.db .\data\game_database_remote.db
        Write-Host "✅ Database copied to .\data\game_database_remote.db" -ForegroundColor Green
        
        # Open with SQLite browser if available
        if (Get-Command "sqlite3" -ErrorAction SilentlyContinue) {
            Write-Host "🔍 Opening database with sqlite3..." -ForegroundColor Cyan
            Write-Host "Type .tables to see all tables, .quit to exit" -ForegroundColor Yellow
            sqlite3 .\data\game_database_remote.db
        } else {
            Write-Host "💡 Install sqlite3 to interact with database directly" -ForegroundColor Yellow
            Write-Host "   You can also use any SQLite GUI tool to open .\data\game_database_remote.db" -ForegroundColor White
        }
    }
    catch {
        Write-Host "❌ Failed to copy database: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

if ($OpenTunnel) {
    Write-Host "🔗 Opening SSH tunnel to remote server..." -ForegroundColor Yellow
    Write-Host "Local port $LocalPort will be forwarded to remote SQLite" -ForegroundColor Cyan
    
    try {
        # This creates a tunnel, but SQLite doesn't work over network by default
        # Instead, we'll create a simple proxy script on the remote server
        $proxyScript = @"
#!/bin/bash
# Simple SQLite proxy server
while true; do
    nc -l -p 5432 -e 'sqlite3 /home/ubuntu/carebot/data/game_database.db'
done
"@
        
        Write-Host "💡 Note: SQLite doesn't support network connections natively." -ForegroundColor Yellow
        Write-Host "   Use -CopyDatabase to download the database file instead." -ForegroundColor Yellow
        Write-Host "   Or use -RunQuery to execute remote queries via SSH." -ForegroundColor Yellow
    }
    catch {
        Write-Host "❌ Failed to open tunnel: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

if ($RunQuery) {
    if (-not $Query) {
        Write-Host "❌ Please provide a query with -Query parameter" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "📊 Executing query on remote database..." -ForegroundColor Yellow
    Write-Host "Query: $Query" -ForegroundColor Cyan
    
    try {
        # Execute query via SSH
        $result = ssh "$RemoteUser@$RemoteHost" "docker exec carebot-app sqlite3 /app/data/game_database.db `"$Query`""
        
        Write-Host "📋 Query Result:" -ForegroundColor Green
        Write-Host $result -ForegroundColor White
    }
    catch {
        Write-Host "❌ Failed to execute query: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "📋 Database Access Commands:" -ForegroundColor Cyan
Write-Host "  View tables: .\db-access.ps1 -RunQuery '.tables'" -ForegroundColor White
Write-Host "  View missions: .\db-access.ps1 -RunQuery 'SELECT * FROM mission_stack;'" -ForegroundColor White
Write-Host "  View battles: .\db-access.ps1 -RunQuery 'SELECT * FROM battles;'" -ForegroundColor White
Write-Host "  Copy DB locally: .\db-access.ps1 -CopyDatabase" -ForegroundColor White
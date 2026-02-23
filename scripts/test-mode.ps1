# CareBot Local Test Mode Script
# Скрипт для запуска бота локально в debug режиме с mock базой данных

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "status", "debug")]
    [string]$Action = "start"
)

$botScript = "CareBot\run_bot.py"
$processName = "python"
$testPort = "5556"

Write-Host "🧪 CareBot Local Test Mode Manager" -ForegroundColor Cyan
Write-Host "Action: $Action" -ForegroundColor Yellow

# Функция для проверки Python
function Test-Python {
    try {
        python --version | Out-Null
        return $true
    } catch {
        Write-Host "❌ Python не найден в PATH!" -ForegroundColor Red
        Write-Host "Установите Python или добавьте его в PATH" -ForegroundColor Yellow
        return $false
    }
}

# Проверяем Python
if (-not (Test-Python)) {
    exit 1
}

switch ($Action.ToLower()) {
    "start" {
        Write-Host "Starting CareBot in local test mode..." -ForegroundColor Green
        
        # Check mock_sqlite_helper.py exists
        if (-not (Test-Path "CareBot\CareBot\mock_sqlite_helper.py")) {
            Write-Host "ERROR: mock_sqlite_helper.py not found!" -ForegroundColor Red
            Write-Host "Make sure the file is created at CareBot\CareBot\mock_sqlite_helper.py" -ForegroundColor Yellow
            exit 1
        }
        
        # Check bot script exists
        if (-not (Test-Path $botScript)) {
            Write-Host "ERROR: $botScript not found!" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Local test mode configuration:" -ForegroundColor Cyan
        Write-Host "  • CAREBOT_TEST_MODE=true" -ForegroundColor White
        Write-Host "  • Telegram Token: TELEGRAM_BOT_TOKEN_TEST" -ForegroundColor White
        Write-Host "  • Mode: Local Python Process" -ForegroundColor White
        Write-Host "  • Mock Database: Enabled" -ForegroundColor White
        
        # Set environment variable for test mode
        $env:CAREBOT_TEST_MODE = "true"
        
        Write-Host "Starting Python bot locally..." -ForegroundColor Green
        Write-Host "Logs will be visible in console. Press Ctrl+C to stop." -ForegroundColor Yellow
        
        # Change to bot directory and run
        Push-Location "CareBot"
        try {
            python run_bot.py
        } catch {
            Write-Host "ERROR starting bot: $($_.Exception.Message)" -ForegroundColor Red
        } finally {
            Pop-Location
        }
    }
    
    "stop" {
        Write-Host "Stop local CareBot processes..." -ForegroundColor Yellow
        
        # Find Python processes with CareBot
        $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*run_bot.py*" -or $_.CommandLine -like "*CareBot*"
        }
        
        if ($processes) {
            foreach ($process in $processes) {
                Write-Host "Stopping process $($process.Id)..." -ForegroundColor Yellow
                $process | Stop-Process -Force
            }
            Write-Host "Local CareBot processes stopped" -ForegroundColor Green
        } else {
            Write-Host "No active CareBot processes found" -ForegroundColor Blue
        }
    }
    
    "status" {
        Write-Host "CareBot Local Test Mode status:" -ForegroundColor Cyan
        
        # Check environment variable
        if ($env:CAREBOT_TEST_MODE -eq "true") {
            Write-Host "TEST_MODE: ENABLED" -ForegroundColor Green
        } else {
            Write-Host "TEST_MODE: NOT SET" -ForegroundColor Yellow
        }
        
        # Check file existence
        if (Test-Path "CareBot\CareBot\mock_sqlite_helper.py") {
            Write-Host "Mock helper: FOUND" -ForegroundColor Green
        } else {
            Write-Host "Mock helper: NOT FOUND" -ForegroundColor Red
        }
        
        if (Test-Path $botScript) {
            Write-Host "Bot script: FOUND" -ForegroundColor Green
        } else {
            Write-Host "Bot script: NOT FOUND" -ForegroundColor Red
        }
        
        # Check active processes
        $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*run_bot.py*" -or $_.CommandLine -like "*CareBot*"
        }
        
        if ($processes) {
            Write-Host "Active processes: $($processes.Count)" -ForegroundColor Green
            foreach ($process in $processes) {
                Write-Host "  PID: $($process.Id)" -ForegroundColor White
            }
        } else {
            Write-Host "Active processes: NONE" -ForegroundColor Yellow
        }
    }
    
    "debug" {
        Write-Host "Debug information:" -ForegroundColor Cyan
        
        Write-Host "`nFile structure:" -ForegroundColor Yellow
        if (Test-Path "CareBot") {
            Write-Host "  CareBot/ - OK" -ForegroundColor Green
            if (Test-Path "CareBot\run_bot.py") {
                Write-Host "    run_bot.py - OK" -ForegroundColor Green
            }
            if (Test-Path "CareBot\CareBot") {
                Write-Host "    CareBot/ - OK" -ForegroundColor Green
                if (Test-Path "CareBot\CareBot\mock_sqlite_helper.py") {
                    Write-Host "      mock_sqlite_helper.py - OK" -ForegroundColor Green
                } else {
                    Write-Host "      mock_sqlite_helper.py - MISSING" -ForegroundColor Red
                }
                if (Test-Path "CareBot\CareBot\config.py") {
                    Write-Host "      config.py - OK" -ForegroundColor Green
                } else {
                    Write-Host "      config.py - MISSING" -ForegroundColor Red
                }
            }
        }
        
        Write-Host "`nPython information:" -ForegroundColor Yellow
        try {
            $pythonVersion = python --version
            Write-Host "  $pythonVersion" -ForegroundColor Green
        } catch {
            Write-Host "  Python not found" -ForegroundColor Red
        }
        
        Write-Host "`nEnvironment Variables:" -ForegroundColor Yellow
        Write-Host "  CAREBOT_TEST_MODE = $($env:CAREBOT_TEST_MODE)" -ForegroundColor White
        
        Write-Host "`nTo start test mode:" -ForegroundColor Cyan
        Write-Host "  .\scripts\test-mode.ps1 start" -ForegroundColor White
    }
    
    default {
        Write-Host "Unknown command: $Action" -ForegroundColor Red
        Write-Host "`nAvailable commands for local mode:" -ForegroundColor Yellow
        Write-Host "  start   - Start local test mode" -ForegroundColor White
        Write-Host "  stop    - Stop local processes" -ForegroundColor White
        Write-Host "  status  - Check status" -ForegroundColor White
        Write-Host "  debug   - Show debug information" -ForegroundColor White
    }
}
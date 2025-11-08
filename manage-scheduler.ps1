# Scraper Scheduler Management Script
# PowerShell script pentru management scheduler

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "test", "config", "cleanup", "stats", "help")]
    [string]$Action = "help",
    
    [Parameter()]
    [switch]$Now,
    
    [Parameter()]
    [string]$Schedule = "daily_weekdays",
    
    [Parameter()]
    [int]$Hour = 14,
    
    [Parameter()]
    [string]$Days = "1-4"
)

$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Text)
    Write-Host "`n$('='*70)" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "$('='*70)`n" -ForegroundColor Cyan
}

function Show-Help {
    Write-Header "🕐 Scraper Scheduler Management"
    
    Write-Host "Usage: .\manage-scheduler.ps1 <action> [options]`n"
    
    Write-Host "Actions:" -ForegroundColor Yellow
    Write-Host "  start       Start scheduler service"
    Write-Host "  stop        Stop scheduler service"
    Write-Host "  restart     Restart scheduler service"
    Write-Host "  status      Show scheduler status"
    Write-Host "  logs        Show scheduler logs (follow mode)"
    Write-Host "  test        Run scraping immediately (test mode)"
    Write-Host "  config      Show current configuration"
    Write-Host "  cleanup     Cleanup old duplicate files from rezultate/"
    Write-Host "  stats       Show storage statistics"
    Write-Host "  help        Show this help message`n"
    
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -Schedule   Schedule type: daily_weekdays, weekly, custom"
    Write-Host "  -Hour       Hour to run (0-23)"
    Write-Host "  -Days       Days to run (e.g., '1-4' for Mon-Thu)"
    Write-Host "  -Now        Run immediately (for test action)`n"
    
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  # Start scheduler with default settings (Mon-Thu at 14:00)"
    Write-Host "  .\manage-scheduler.ps1 start`n"
    
    Write-Host "  # Start with custom schedule (Mon-Fri at 10:00)"
    Write-Host "  .\manage-scheduler.ps1 start -Schedule daily_weekdays -Hour 10 -Days '1-5'`n"
    
    Write-Host "  # Run scraping immediately"
    Write-Host "  .\manage-scheduler.ps1 test -Now`n"
    
    Write-Host "  # View logs"
    Write-Host "  .\manage-scheduler.ps1 logs`n"
    
    Write-Host "  # Check status"
    Write-Host "  .\manage-scheduler.ps1 status`n"
}

function Start-Scheduler {
    Write-Header "🚀 Starting Scraper Scheduler"
    
    # Set environment variables
    $env:SCRAPER_ENABLED = "true"
    $env:SCRAPER_SCHEDULE_TYPE = $Schedule
    $env:SCRAPER_HOUR = $Hour
    $env:SCRAPER_DAYS = $Days
    $env:SCRAPER_DELAY = "2.0"
    $env:SCRAPER_AUTO_IMPORT = "true"
    $env:SCRAPER_API_URL = "http://localhost:8000"
    
    Write-Host "Configuration:" -ForegroundColor Yellow
    Write-Host "  Schedule Type: $Schedule"
    Write-Host "  Hour: $Hour"
    Write-Host "  Days: $Days`n"
    
    # Check if API is running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
        Write-Host "✅ API is running" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Warning: API is not running. Auto-import will fail." -ForegroundColor Yellow
        Write-Host "   Start API with: cd db_service && docker-compose up -d`n"
    }
    
    # Check if links file exists
    if (Test-Path "linkuri_legislatie.txt") {
        $linkCount = (Get-Content "linkuri_legislatie.txt" | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '\S' }).Count
        Write-Host "✅ Found $linkCount links in linkuri_legislatie.txt" -ForegroundColor Green
    } else {
        Write-Host "❌ Error: linkuri_legislatie.txt not found!" -ForegroundColor Red
        return
    }
    
    Write-Host "`n🔄 Starting scheduler..." -ForegroundColor Cyan
    Write-Host "   Press Ctrl+C to stop`n"
    
    python scheduler.py
}

function Stop-Scheduler {
    Write-Header "🛑 Stopping Scraper Scheduler"
    
    # Find Python processes running scheduler.py
    $processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*scheduler.py*"
    }
    
    if ($processes) {
        Write-Host "Found $($processes.Count) scheduler process(es)"
        $processes | ForEach-Object {
            Write-Host "  Stopping process $($_.Id)..."
            Stop-Process -Id $_.Id -Force
        }
        Write-Host "✅ Scheduler stopped" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  No scheduler process found" -ForegroundColor Yellow
    }
}

function Get-SchedulerStatus {
    Write-Header "📊 Scheduler Status"
    
    # Check if process is running
    $processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*scheduler.py*"
    }
    
    if ($processes) {
        Write-Host "Status: " -NoNewline
        Write-Host "RUNNING" -ForegroundColor Green
        Write-Host "`nProcesses:"
        $processes | ForEach-Object {
            Write-Host "  PID: $($_.Id)"
            Write-Host "  Memory: $([math]::Round($_.WorkingSet64/1MB, 2)) MB"
            Write-Host "  Start Time: $($_.StartTime)"
        }
    } else {
        Write-Host "Status: " -NoNewline
        Write-Host "STOPPED" -ForegroundColor Red
    }
    
    # Check last log
    if (Test-Path "scraper_scheduler.log") {
        Write-Host "`nLast 5 log entries:" -ForegroundColor Yellow
        Get-Content "scraper_scheduler.log" -Tail 5
    }
}

function Show-Logs {
    Write-Header "📄 Scheduler Logs"
    
    if (Test-Path "scraper_scheduler.log") {
        Write-Host "Following logs (Ctrl+C to exit)...`n" -ForegroundColor Cyan
        Get-Content "scraper_scheduler.log" -Wait -Tail 50
    } else {
        Write-Host "❌ Log file not found" -ForegroundColor Red
    }
}

function Test-Scraper {
    Write-Header "🧪 Test Mode - Running Scraper Now"
    
    if ($Now) {
        Write-Host "Running scraping job immediately...`n" -ForegroundColor Cyan
        python scheduler.py --now
    } else {
        Write-Host "Testing configuration...`n" -ForegroundColor Cyan
        python scheduler.py --show-config
    }
}

function Show-Config {
    Write-Header "⚙️  Current Configuration"
    
    python scheduler.py --show-config
}

function Cleanup-Files {
    Write-Header "🧹 Cleanup Old Files"
    
    Write-Host "Running cleanup (removes duplicate files, keeps latest per act)...`n" -ForegroundColor Cyan
    python cleanup_files.py --execute
}

function Show-Stats {
    Write-Header "📊 Storage Statistics"
    
    python cleanup_files.py --stats
}

# Main execution
switch ($Action) {
    "start" { Start-Scheduler }
    "stop" { Stop-Scheduler }
    "restart" {
        Stop-Scheduler
        Start-Sleep -Seconds 2
        Start-Scheduler
    }
    "status" { Get-SchedulerStatus }
    "logs" { Show-Logs }
    "test" { Test-Scraper }
    "config" { Show-Config }
    "cleanup" { Cleanup-Files }
    "stats" { Show-Stats }
    "help" { Show-Help }
    default { Show-Help }
}

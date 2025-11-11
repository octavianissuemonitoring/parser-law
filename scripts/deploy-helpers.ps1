# Parser Law - PowerShell Deployment Helpers
# Add to your PowerShell profile: notepad $PROFILE

function Deploy-ParserLaw {
    <#
    .SYNOPSIS
        Deploy Parser Law application to VPS
    .DESCRIPTION
        Commits, pushes to GitHub, and deploys to production VPS with automatic backup and health check
    .EXAMPLE
        Deploy-ParserLaw
        deploy  # Using alias
    #>
    
    param(
        [string]$Message = "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    )
    
    Write-Host "🚀 Starting deployment process..." -ForegroundColor Green
    Write-Host ""
    
    # Check for uncommitted changes
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        Write-Host "📝 Uncommitted changes detected:" -ForegroundColor Yellow
        git status --short
        Write-Host ""
        
        $commit = Read-Host "Commit these changes? (Y/n)"
        if ($commit -ne 'n' -and $commit -ne 'N') {
            git add .
            git commit -m $Message
        }
    }
    
    # Push to GitHub
    Write-Host "📤 Pushing to GitHub..." -ForegroundColor Yellow
    git push origin master
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to push to GitHub!" -ForegroundColor Red
        return
    }
    
    Write-Host "✅ Pushed to GitHub" -ForegroundColor Green
    Write-Host ""
    
    # Deploy to VPS
    Write-Host "📦 Deploying to VPS (77.237.235.158)..." -ForegroundColor Yellow
    ssh root@77.237.235.158 '/opt/parser-law/scripts/deploy.sh'
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Deployment successful!" -ForegroundColor Green
        Write-Host "🌐 Live at: https://legislatie.issuemonitoring.ro/docs" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Deployment failed!" -ForegroundColor Red
        Write-Host "💡 Run 'rollback' to revert to previous version" -ForegroundColor Yellow
    }
}

function Rollback-ParserLaw {
    <#
    .SYNOPSIS
        Rollback Parser Law deployment on VPS
    .DESCRIPTION
        Restores previous version from backup with automatic health check
    .PARAMETER BackupPath
        Specific backup path, or 'last' for most recent backup
    .EXAMPLE
        Rollback-ParserLaw
        Rollback-ParserLaw -BackupPath "last"
        rollback  # Using alias
    #>
    
    param(
        [string]$BackupPath = "last"
    )
    
    Write-Host "🔄 Rolling back deployment on VPS..." -ForegroundColor Yellow
    Write-Host ""
    
    ssh root@77.237.235.158 "/opt/parser-law/scripts/rollback.sh $BackupPath"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Rollback successful!" -ForegroundColor Green
        Write-Host "🌐 Check: https://legislatie.issuemonitoring.ro/health" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Rollback failed!" -ForegroundColor Red
    }
}

function Get-ParserLawBackups {
    <#
    .SYNOPSIS
        List available backups on VPS
    .DESCRIPTION
        Shows all available deployment backups with commit hashes
    .EXAMPLE
        Get-ParserLawBackups
        backups  # Using alias
    #>
    
    Write-Host "📦 Available backups on VPS:" -ForegroundColor Yellow
    Write-Host ""
    ssh root@77.237.235.158 '/opt/parser-law/scripts/rollback.sh'
}

function Get-ParserLawStatus {
    <#
    .SYNOPSIS
        Check Parser Law service status on VPS
    .DESCRIPTION
        Shows Docker container status and health check
    .EXAMPLE
        Get-ParserLawStatus
        status  # Using alias
    #>
    
    Write-Host "📊 Service Status on VPS:" -ForegroundColor Yellow
    Write-Host ""
    
    ssh root@77.237.235.158 'cd /opt/parser-law/db_service && docker compose ps && echo "" && curl -s http://localhost:8000/health | jq .'
    
    Write-Host ""
    Write-Host "🌐 Live URLs:" -ForegroundColor Cyan
    Write-Host "  Health: https://legislatie.issuemonitoring.ro/health" -ForegroundColor Gray
    Write-Host "  Docs:   https://legislatie.issuemonitoring.ro/docs" -ForegroundColor Gray
}

function Get-ParserLawLogs {
    <#
    .SYNOPSIS
        Show Parser Law application logs from VPS
    .DESCRIPTION
        Tails application logs from Docker containers
    .PARAMETER Service
        Service to show logs for: api, postgres, scheduler, or all
    .PARAMETER Lines
        Number of recent lines to show (default: 50)
    .EXAMPLE
        Get-ParserLawLogs -Service api
        logs api  # Using alias
    #>
    
    param(
        [ValidateSet('api', 'postgres', 'scheduler', 'all')]
        [string]$Service = 'api',
        [int]$Lines = 50
    )
    
    Write-Host "📋 Showing logs for: $Service" -ForegroundColor Yellow
    Write-Host ""
    
    if ($Service -eq 'all') {
        ssh root@77.237.235.158 "cd /opt/parser-law/db_service && docker compose logs --tail=$Lines"
    } elseif ($Service -eq 'scheduler') {
        ssh root@77.237.235.158 "cd /opt/parser-law && docker compose -f docker-compose.scheduler.yml logs --tail=$Lines"
    } else {
        ssh root@77.237.235.158 "cd /opt/parser-law/db_service && docker compose logs --tail=$Lines $Service"
    }
}

# Aliases
Set-Alias deploy Deploy-ParserLaw
Set-Alias rollback Rollback-ParserLaw
Set-Alias backups Get-ParserLawBackups
Set-Alias status Get-ParserLawStatus
Set-Alias logs Get-ParserLawLogs

# Export functions
Export-ModuleMember -Function Deploy-ParserLaw, Rollback-ParserLaw, Get-ParserLawBackups, Get-ParserLawStatus, Get-ParserLawLogs
Export-ModuleMember -Alias deploy, rollback, backups, status, logs

Write-Host "✅ Parser Law deployment helpers loaded!" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands:" -ForegroundColor Yellow
Write-Host "  deploy              - Deploy to production" -ForegroundColor Gray
Write-Host "  rollback            - Rollback to previous version" -ForegroundColor Gray
Write-Host "  backups             - List available backups" -ForegroundColor Gray
Write-Host "  status              - Check service status" -ForegroundColor Gray
Write-Host "  logs [service]      - View application logs" -ForegroundColor Gray
Write-Host ""

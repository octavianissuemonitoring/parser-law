# Sync VPS database to LOCAL
# Usage: .\scripts\sync_vps_to_local.ps1

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$tempDir = "c:\Users\octavian\scraper\parser_law\parser-law\data\backups"
$vpsHost = "109.123.249.228"

# Create temp directory
if(!(Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
}

Write-Host "`n=== Syncing VPS Database to Local ===" -ForegroundColor Cyan
Write-Host "Timestamp: $timestamp`n" -ForegroundColor Gray

# Step 1: Export VPS articole table
Write-Host "[1/4] Exporting VPS articole..." -ForegroundColor Yellow
$dumpFile = "$tempDir\articole_vps_$timestamp.sql"

$sshCommand = "docker exec legislatie_postgres pg_dump -U legislatie_user -d monitoring_platform --schema=legislatie --table=legislatie.articole --data-only --column-inserts --on-conflict-do-nothing"
ssh root@$vpsHost $sshCommand | Out-File -Encoding UTF8 $dumpFile

if(!(Test-Path $dumpFile)) {
    Write-Host "✗ Failed to export VPS data" -ForegroundColor Red
    exit 1
}

$fileSize = (Get-Item $dumpFile).Length / 1MB
Write-Host "  ✓ Exported: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Green

# Step 2: Backup local articole
Write-Host "`n[2/4] Backing up LOCAL articole..." -ForegroundColor Yellow
$backupFile = "$tempDir\articole_local_backup_$timestamp.sql"

docker exec legislatie_postgres pg_dump -U legislatie_user -d monitoring_platform `
  --schema=legislatie `
  --table=legislatie.articole `
  --data-only `
  --column-inserts | Out-File -Encoding UTF8 $backupFile

Write-Host "  ✓ Backup saved: articole_local_backup_$timestamp.sql" -ForegroundColor Green

# Step 3: Get current counts
Write-Host "`n[3/4] Comparing data..." -ForegroundColor Yellow

$localCountRaw = (docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -t -c "SELECT COUNT(*) FROM legislatie.articole") -join ''
$vpsCountRaw = (ssh root@$vpsHost "docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -t -c 'SELECT COUNT(*) FROM legislatie.articole'") -join ''

$localCount = [int]($localCountRaw.Trim())
$vpsCount = [int]($vpsCountRaw.Trim())
$difference = $vpsCount - $localCount

Write-Host "  Local articles: $localCount" -ForegroundColor Cyan
Write-Host "  VPS articles:   $vpsCount" -ForegroundColor Cyan
Write-Host "  Difference:     $difference articles missing locally" -ForegroundColor Yellow

# Step 4: Import VPS data to local
Write-Host "`n[4/4] Importing VPS data to LOCAL..." -ForegroundColor Yellow
Write-Host "  This will TRUNCATE local articole table and import fresh data!" -ForegroundColor Red
$confirm = Read-Host "  Continue? (yes/no)"

if($confirm -ne "yes") {
    Write-Host "`n✗ Sync cancelled by user" -ForegroundColor Yellow
    exit 0
}

# Truncate local articole and reset sequence
Write-Host "`n  Truncating local articole table..." -ForegroundColor Gray
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "TRUNCATE TABLE legislatie.articole RESTART IDENTITY CASCADE"

# Import VPS dump
Write-Host "  Importing VPS data..." -ForegroundColor Gray
Get-Content $dumpFile | docker exec -i legislatie_postgres psql -U legislatie_user -d monitoring_platform

# Verify import
$newCountRaw = (docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -t -c "SELECT COUNT(*) FROM legislatie.articole") -join ''
$newCount = [int]($newCountRaw.Trim())
Write-Host "`n  ✓ New local count: $newCount articles" -ForegroundColor Green

# Step 5: Verify data quality
Write-Host "`n[5/5] Verifying data quality..." -ForegroundColor Yellow

$stats = docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -t -c @"
SELECT 
  COUNT(*) as total,
  COUNT(capitol_denumire) as cu_capitol,
  COUNT(titlu_denumire) as cu_titlu,
  ROUND(100.0 * COUNT(capitol_denumire) / COUNT(*), 1) as proc_capitol,
  ROUND(100.0 * COUNT(titlu_denumire) / COUNT(*), 1) as proc_titlu
FROM legislatie.articole
"@

Write-Host "  $stats" -ForegroundColor Cyan

Write-Host "`n=== Sync Complete ===" -ForegroundColor Green
Write-Host "VPS data successfully imported to LOCAL!" -ForegroundColor Green
Write-Host "`nBackup location: $backupFile" -ForegroundColor Gray
Write-Host "VPS dump location: $dumpFile" -ForegroundColor Gray
Write-Host ""

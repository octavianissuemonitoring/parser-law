# Script pentru testarea utilizării resurselor cu 3 parsere simultane

$vpsHost = "root@77.237.235.158"
$apiUrl = "http://legislatie.issuemonitoring.ro/api/v1"

# 3 linkuri diferite pentru testare
$links = @(
    "https://legislatie.just.ro/Public/FormaPrintabila/00000G1656LBGXZIRQU152DYXZD7MLAE",  # LEGE 123/2012
    "https://legislatie.just.ro/Public/FormaPrintabila/00000G281FG4CXAJKYN11PHCPS08AG33",  # LEGE 121/2024
    "https://legislatie.just.ro/Public/FormaPrintabila/00000G2Z5JMZWFBWI5O1SNEEF3HS8YTF"   # Alt act
)

Write-Host "🚀 Starting concurrent parser test..." -ForegroundColor Green
Write-Host ""

# 1. Șterg baza de date
Write-Host "🗑️  Clearing database..." -ForegroundColor Yellow
ssh $vpsHost "docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c 'TRUNCATE TABLE legislatie.acte_legislative CASCADE; TRUNCATE TABLE legislatie.linkuri_legislatie;'" 2>$null

# 2. Capturez resurse ÎNAINTE
Write-Host ""
Write-Host "📊 Resources BEFORE processing:" -ForegroundColor Cyan
$beforeStats = ssh $vpsHost "free -h | grep Mem && df -h / | grep /dev && docker stats --no-stream --format 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}'" 2>$null
Write-Host $beforeStats

# 3. Adaug cele 3 linkuri
Write-Host ""
Write-Host "➕ Adding 3 links..." -ForegroundColor Yellow
foreach ($link in $links) {
    $body = @{ url = $link } | ConvertTo-Json
    Invoke-RestMethod -Uri "$apiUrl/links/" -Method Post -Body $body -ContentType "application/json" | Out-Null
}

# 4. Procesez toate cele 3 linkuri SIMULTAN (3 joburi paralele)
Write-Host ""
Write-Host "⚙️  Processing 3 links SIMULTANEOUSLY..." -ForegroundColor Green

$jobs = @()
for ($i = 0; $i -lt 3; $i++) {
    $link = $links[$i]
    $jobs += Start-Job -ScriptBlock {
        param($apiUrl, $link)
        $encodedUrl = [System.Uri]::EscapeDataString($link)
        try {
            Invoke-RestMethod -Uri "$apiUrl/links/process?url=$encodedUrl" -Method Post -ErrorAction Stop
        } catch {
            Write-Error "Failed to process link: $_"
        }
    } -ArgumentList $apiUrl, $link
}

Write-Host "⏱️  Waiting for parsers to start (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 5. Capturez resurse DURING processing
Write-Host ""
Write-Host "📊 Resources DURING processing (peak load):" -ForegroundColor Cyan
$duringStats = ssh $vpsHost "free -h | grep Mem && df -h / | grep /dev && docker stats --no-stream --format 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}'" 2>$null
Write-Host $duringStats

# 6. Aștept finalizarea joburilor
Write-Host ""
Write-Host "⏱️  Waiting for all parsers to complete..." -ForegroundColor Yellow
$jobs | Wait-Job | Out-Null
$jobs | Remove-Job

Write-Host ""
Write-Host "⏱️  Waiting additional 30 seconds for import completion..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 7. Capturez resurse DUPĂ
Write-Host ""
Write-Host "📊 Resources AFTER processing:" -ForegroundColor Cyan
$afterStats = ssh $vpsHost "free -h | grep Mem && df -h / | grep /dev && docker stats --no-stream --format 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}'" 2>$null
Write-Host $afterStats

# 8. Verific rezultatele
Write-Host ""
Write-Host "✅ Processing results:" -ForegroundColor Green
$results = ssh $vpsHost "docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c 'SELECT COUNT(*) as total_acts FROM legislatie.acte_legislative; SELECT id, status, acte_count FROM legislatie.linkuri_legislatie ORDER BY id;'" 2>$null
Write-Host $results

Write-Host ""
Write-Host "🎉 Test completed!" -ForegroundColor Green

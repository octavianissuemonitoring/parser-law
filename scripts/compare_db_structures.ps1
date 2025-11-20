# Compare LOCAL and VPS database structures
# Usage: .\scripts\compare_db_structures.ps1

$vpsHost = "109.123.249.228"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportDir = "c:\Users\octavian\scraper\parser_law\parser-law\data\export"

if(!(Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

Write-Host "`n=== Comparing LOCAL vs VPS Database Structures ===" -ForegroundColor Cyan
Write-Host "Timestamp: $timestamp`n" -ForegroundColor Gray

# Tables to compare
$tables = @(
    'acte_legislative',
    'articole',
    'anexe',
    'domenii',
    'issues',
    'acte_domenii',
    'articole_domenii',
    'acte_issues',
    'articole_issues',
    'anexe_issues',
    'structure_issues',
    'acte_modificari',
    'articole_modificari',
    'linkuri_legislatie'
)

$allResults = @()
$differences = @()

foreach($table in $tables) {
    Write-Host "Checking table: $table" -ForegroundColor Yellow
    
    # Get LOCAL structure
    $localStructure = docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\d legislatie.$table" 2>&1
    
    # Get VPS structure
    $vpsStructure = ssh root@$vpsHost "docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c '\d legislatie.$table'" 2>&1
    
    # Save structures to files
    $localStructure | Out-File -Encoding UTF8 "$reportDir\local_$table`_structure.txt"
    $vpsStructure | Out-File -Encoding UTF8 "$reportDir\vps_$table`_structure.txt"
    
    # Compare
    $localText = ($localStructure -join "`n").Trim()
    $vpsText = ($vpsStructure -join "`n").Trim()
    
    if($localText -eq $vpsText) {
        Write-Host "  ✓ IDENTICAL" -ForegroundColor Green
        $allResults += [PSCustomObject]@{
            Table = $table
            Status = "IDENTICAL"
            Difference = ""
        }
    } else {
        Write-Host "  ✗ DIFFERENT!" -ForegroundColor Red
        $differences += $table
        
        # Try to identify what's different
        $localLines = $localText -split "`n"
        $vpsLines = $vpsText -split "`n"
        
        $diff = ""
        if($localLines.Count -ne $vpsLines.Count) {
            $diff += "Line count: LOCAL=$($localLines.Count) vs VPS=$($vpsLines.Count); "
        }
        
        # Find specific column differences
        $localCols = $localLines | Where-Object { $_ -match '^\s+\w+\s+\|' }
        $vpsCols = $vpsLines | Where-Object { $_ -match '^\s+\w+\s+\|' }
        
        $localColNames = $localCols | ForEach-Object { ($_ -split '\|')[0].Trim() }
        $vpsColNames = $vpsCols | ForEach-Object { ($_ -split '\|')[0].Trim() }
        
        $missingInLocal = $vpsColNames | Where-Object { $localColNames -notcontains $_ }
        $missingInVps = $localColNames | Where-Object { $vpsColNames -notcontains $_ }
        
        if($missingInLocal) {
            $diff += "Missing in LOCAL: $($missingInLocal -join ', '); "
        }
        if($missingInVps) {
            $diff += "Missing in VPS: $($missingInVps -join ', '); "
        }
        
        $allResults += [PSCustomObject]@{
            Table = $table
            Status = "DIFFERENT"
            Difference = $diff
        }
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Total tables checked: $($tables.Count)" -ForegroundColor White
Write-Host "Identical: $($tables.Count - $differences.Count)" -ForegroundColor Green
Write-Host "Different: $($differences.Count)" -ForegroundColor $(if($differences.Count -gt 0) { "Red" } else { "Green" })

if($differences.Count -gt 0) {
    Write-Host "`nTables with differences:" -ForegroundColor Red
    foreach($diff in $differences) {
        Write-Host "  - $diff" -ForegroundColor Yellow
    }
}

# Generate detailed report
Write-Host "`nGenerating detailed report..." -ForegroundColor Yellow

$reportFile = "$reportDir\db_comparison_report_$timestamp.txt"
$htmlReportFile = "$reportDir\db_comparison_report_$timestamp.html"

# Text report
@"
=============================================================================
DATABASE STRUCTURE COMPARISON REPORT
=============================================================================
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
LOCAL: Docker container legislatie_postgres (localhost:5432)
VPS: $vpsHost (legislatie_postgres container)

-----------------------------------------------------------------------------
SUMMARY
-----------------------------------------------------------------------------
Total tables: $($tables.Count)
Identical: $($tables.Count - $differences.Count)
Different: $($differences.Count)

-----------------------------------------------------------------------------
TABLE-BY-TABLE RESULTS
-----------------------------------------------------------------------------
$($allResults | ForEach-Object {
"Table: $($_.Table)
Status: $($_.Status)
$(if($_.Difference) { "Difference: $($_.Difference)" })
"
})

-----------------------------------------------------------------------------
RECOMMENDATIONS
-----------------------------------------------------------------------------
$(if($differences.Count -eq 0) {
"✓ All database structures are identical between LOCAL and VPS.
  No migration or synchronization needed."
} else {
"✗ Found $($differences.Count) table(s) with structural differences.
  
  ACTION REQUIRED:
  1. Review detailed differences in files: local_*_structure.txt vs vps_*_structure.txt
  2. Identify if differences are due to:
     - Missing migrations (run alembic upgrade head)
     - Schema drift (regenerate models from DB)
     - Manual changes not tracked (create new migration)
  3. Apply fixes to ensure parity before production deployment
"
})

-----------------------------------------------------------------------------
DETAILED STRUCTURE FILES
-----------------------------------------------------------------------------
Location: $reportDir
Files generated:
$($tables | ForEach-Object { "  - local_$_`_structure.txt`n  - vps_$_`_structure.txt" })

=============================================================================
"@ | Out-File -Encoding UTF8 $reportFile

Write-Host "  ✓ Text report: $reportFile" -ForegroundColor Green

# HTML report
$htmlContent = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Database Structure Comparison Report</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }
        .summary-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
        .summary-card.green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
        .summary-card.red { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
        .summary-card h3 { margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }
        .summary-card .number { font-size: 36px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; font-weight: 600; }
        tr:hover { background: #f8f9fa; }
        .status-identical { color: #27ae60; font-weight: bold; }
        .status-different { color: #e74c3c; font-weight: bold; }
        .difference { font-size: 12px; color: #7f8c8d; font-style: italic; }
        .info-box { background: #e8f4f8; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .warning-box { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .success-box { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .error-box { background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; border-radius: 4px; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }
        .timestamp { color: #95a5a6; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Database Structure Comparison Report</h1>
        <p class="timestamp">Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
        
        <div class="info-box">
            <strong>Comparison:</strong><br>
            <code>LOCAL</code>: Docker container legislatie_postgres (localhost:5432)<br>
            <code>VPS</code>: $vpsHost (legislatie_postgres container)
        </div>
        
        <h2>📊 Summary</h2>
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tables</h3>
                <div class="number">$($tables.Count)</div>
            </div>
            <div class="summary-card green">
                <h3>Identical</h3>
                <div class="number">$($tables.Count - $differences.Count)</div>
            </div>
            <div class="summary-card $(if($differences.Count -gt 0) { 'red' } else { 'green' })">
                <h3>Different</h3>
                <div class="number">$($differences.Count)</div>
            </div>
        </div>
        
        $(if($differences.Count -eq 0) {
            '<div class="success-box"><strong>✓ SUCCESS:</strong> All database structures are identical between LOCAL and VPS. No migration or synchronization needed.</div>'
        } else {
            '<div class="error-box"><strong>✗ WARNING:</strong> Found ' + $differences.Count + ' table(s) with structural differences. Review required!</div>'
        })
        
        <h2>📋 Table-by-Table Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Table Name</th>
                    <th>Status</th>
                    <th>Differences</th>
                </tr>
            </thead>
            <tbody>
                $($allResults | ForEach-Object {
                    $statusClass = if($_.Status -eq "IDENTICAL") { "status-identical" } else { "status-different" }
                    "<tr>
                        <td><code>$($_.Table)</code></td>
                        <td class='$statusClass'>$($_.Status)</td>
                        <td class='difference'>$($_.Difference)</td>
                    </tr>"
                })
            </tbody>
        </table>
        
        $(if($differences.Count -gt 0) {
            "<h2>⚠️ Action Required</h2>
            <div class='warning-box'>
                <ol>
                    <li>Review detailed differences in files: <code>local_*_structure.txt</code> vs <code>vps_*_structure.txt</code></li>
                    <li>Identify if differences are due to:
                        <ul>
                            <li>Missing migrations (run <code>alembic upgrade head</code>)</li>
                            <li>Schema drift (regenerate models from DB)</li>
                            <li>Manual changes not tracked (create new migration)</li>
                        </ul>
                    </li>
                    <li>Apply fixes to ensure parity before production deployment</li>
                </ol>
            </div>"
        })
        
        <h2>📁 Detailed Structure Files</h2>
        <p>Location: <code>$reportDir</code></p>
        <ul>
            $($tables | ForEach-Object { 
                "<li><code>local_$_`_structure.txt</code> vs <code>vps_$_`_structure.txt</code></li>"
            })
        </ul>
    </div>
</body>
</html>
"@

$htmlContent | Out-File -Encoding UTF8 $htmlReportFile
Write-Host "  ✓ HTML report: $htmlReportFile" -ForegroundColor Green

Write-Host "`n=== Comparison Complete ===" -ForegroundColor Green
Write-Host "Reports saved to: $reportDir" -ForegroundColor Cyan
Write-Host ""

# Open HTML report in browser
if($differences.Count -gt 0) {
    Write-Host "Opening HTML report in browser..." -ForegroundColor Yellow
    Start-Process $htmlReportFile
}

return $allResults

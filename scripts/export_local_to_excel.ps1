# Export LOCAL database to Excel
# Usage: .\export_local_to_excel.ps1

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$exportDir = "c:\Users\octavian\scraper\parser_law\parser-law\data\export"

# Create export directory
if(!(Test-Path $exportDir)) {
    New-Item -ItemType Directory -Path $exportDir -Force | Out-Null
}

Write-Host "`n=== Exporting LOCAL Database ===" -ForegroundColor Cyan

# Export acte_legislative
Write-Host "`nExporting acte_legislative..." -ForegroundColor Yellow
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\copy (SELECT id, tip_act, nr_act, data_act, an_act, titlu_act, emitent_act, mof_nr, mof_data, mof_an, ai_status, ai_processed_at, export_status, versiune, created_at FROM legislatie.acte_legislative ORDER BY id) TO STDOUT WITH CSV HEADER" | Out-File -Encoding UTF8 "$exportDir\acte_legislative_local_$timestamp.csv"

# Export articole
Write-Host "Exporting articole..." -ForegroundColor Yellow
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\copy (SELECT id, act_id, articol_nr, articol_label, titlu_nr, titlu_denumire, capitol_nr, capitol_denumire, sectiune_nr, sectiune_denumire, subsectiune_nr, subsectiune_denumire, text_articol, explicatie, ordine, ai_status, ai_processed_at, created_at FROM legislatie.articole ORDER BY act_id, ordine, id) TO STDOUT WITH CSV HEADER" | Out-File -Encoding UTF8 "$exportDir\articole_local_$timestamp.csv"

# Export domenii
Write-Host "Exporting domenii..." -ForegroundColor Yellow
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\copy (SELECT id, denumire, cod, descriere, culoare, ordine, activ, created_at FROM legislatie.domenii ORDER BY ordine, id) TO STDOUT WITH CSV HEADER" | Out-File -Encoding UTF8 "$exportDir\domenii_local_$timestamp.csv"

# Export acte_domenii
Write-Host "Exporting acte_domenii..." -ForegroundColor Yellow
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\copy (SELECT ad.id, ad.act_id, ad.domeniu_id, al.titlu_act, d.denumire as domeniu_nume FROM legislatie.acte_domenii ad JOIN legislatie.acte_legislative al ON ad.act_id = al.id JOIN legislatie.domenii d ON ad.domeniu_id = d.id ORDER BY ad.id) TO STDOUT WITH CSV HEADER" | Out-File -Encoding UTF8 "$exportDir\acte_domenii_local_$timestamp.csv"

# Export articole_domenii
Write-Host "Exporting articole_domenii..." -ForegroundColor Yellow
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\copy (SELECT ad.id, ad.articol_id, ad.domeniu_id, art.articol_nr, d.denumire as domeniu_nume FROM legislatie.articole_domenii ad JOIN legislatie.articole art ON ad.articol_id = art.id JOIN legislatie.domenii d ON ad.domeniu_id = d.id ORDER BY ad.id) TO STDOUT WITH CSV HEADER" | Out-File -Encoding UTF8 "$exportDir\articole_domenii_local_$timestamp.csv"

# Export issues
Write-Host "Exporting issues..." -ForegroundColor Yellow
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\copy (SELECT id, denumire, descriere, source, confidence_score, data_creare FROM legislatie.issues ORDER BY id) TO STDOUT WITH CSV HEADER" | Out-File -Encoding UTF8 "$exportDir\issues_local_$timestamp.csv"

# Export articole_issues
Write-Host "Exporting articole_issues..." -ForegroundColor Yellow
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\copy (SELECT ai.id, ai.articol_id, ai.issue_id, ai.domeniu_id, art.articol_nr, d.denumire as domeniu_nume FROM legislatie.articole_issues ai JOIN legislatie.articole art ON ai.articol_id = art.id JOIN legislatie.domenii d ON ai.domeniu_id = d.id ORDER BY ai.id) TO STDOUT WITH CSV HEADER" | Out-File -Encoding UTF8 "$exportDir\articole_issues_local_$timestamp.csv"

# Export acte_issues
Write-Host "Exporting acte_issues..." -ForegroundColor Yellow
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\copy (SELECT ai.id, ai.act_id, ai.issue_id, ai.domeniu_id, al.titlu_act, d.denumire as domeniu_nume FROM legislatie.acte_issues ai JOIN legislatie.acte_legislative al ON ai.act_id = al.id JOIN legislatie.domenii d ON ai.domeniu_id = d.id ORDER BY ai.id) TO STDOUT WITH CSV HEADER" | Out-File -Encoding UTF8 "$exportDir\acte_issues_local_$timestamp.csv"

# Export structure_issues
Write-Host "Exporting structure_issues..." -ForegroundColor Yellow
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\copy (SELECT si.id, si.act_id, si.issue_id, si.domeniu_id, si.titlu_nr, si.capitol_nr, si.sectiune_nr, al.titlu_act, d.denumire as domeniu_nume FROM legislatie.structure_issues si JOIN legislatie.acte_legislative al ON si.act_id = al.id JOIN legislatie.domenii d ON si.domeniu_id = d.id ORDER BY si.id) TO STDOUT WITH CSV HEADER" | Out-File -Encoding UTF8 "$exportDir\structure_issues_local_$timestamp.csv"

Write-Host "`n=== Converting CSV to Excel ===" -ForegroundColor Cyan

# Convert CSV to Excel using Python
python -c @"
import pandas as pd
from pathlib import Path

export_dir = Path(r'$exportDir')
timestamp = '$timestamp'

print('Converting CSV files to Excel...')

# Read CSV files
df_acte = pd.read_csv(export_dir / f'acte_legislative_local_{timestamp}.csv')
df_art = pd.read_csv(export_dir / f'articole_local_{timestamp}.csv')
df_dom = pd.read_csv(export_dir / f'domenii_local_{timestamp}.csv')
df_acte_dom = pd.read_csv(export_dir / f'acte_domenii_local_{timestamp}.csv')
df_art_dom = pd.read_csv(export_dir / f'articole_domenii_local_{timestamp}.csv')
df_issues = pd.read_csv(export_dir / f'issues_local_{timestamp}.csv')
df_art_issues = pd.read_csv(export_dir / f'articole_issues_local_{timestamp}.csv')
df_acte_issues = pd.read_csv(export_dir / f'acte_issues_local_{timestamp}.csv')
df_struct_issues = pd.read_csv(export_dir / f'structure_issues_local_{timestamp}.csv')

print(f'LOCAL DATABASE:')
print(f'  Acte legislative: {len(df_acte)} rows')
print(f'  Articole: {len(df_art)} rows')
print(f'  Domenii: {len(df_dom)} rows')
print(f'  Acte-Domenii: {len(df_acte_dom)} rows')
print(f'  Articole-Domenii: {len(df_art_dom)} rows')
print(f'  Issues: {len(df_issues)} rows')
print(f'  Articole-Issues: {len(df_art_issues)} rows')
print(f'  Acte-Issues: {len(df_acte_issues)} rows')
print(f'  Structure-Issues: {len(df_struct_issues)} rows')

# Create individual Excel files
print('\nCreating individual Excel files...')
df_acte.to_excel(export_dir / f'acte_legislative_local_{timestamp}.xlsx', index=False, engine='openpyxl')
df_art.to_excel(export_dir / f'articole_local_{timestamp}.xlsx', index=False, engine='openpyxl')
df_dom.to_excel(export_dir / f'domenii_local_{timestamp}.xlsx', index=False, engine='openpyxl')
df_acte_dom.to_excel(export_dir / f'acte_domenii_local_{timestamp}.xlsx', index=False, engine='openpyxl')
df_art_dom.to_excel(export_dir / f'articole_domenii_local_{timestamp}.xlsx', index=False, engine='openpyxl')
df_issues.to_excel(export_dir / f'issues_local_{timestamp}.xlsx', index=False, engine='openpyxl')
df_art_issues.to_excel(export_dir / f'articole_issues_local_{timestamp}.xlsx', index=False, engine='openpyxl')
df_acte_issues.to_excel(export_dir / f'acte_issues_local_{timestamp}.xlsx', index=False, engine='openpyxl')
df_struct_issues.to_excel(export_dir / f'structure_issues_local_{timestamp}.xlsx', index=False, engine='openpyxl')

# Create all-in-one workbook
print('Creating combined workbook...')
summary_file = export_dir / f'database_export_LOCAL_all_{timestamp}.xlsx'
with pd.ExcelWriter(summary_file, engine='openpyxl') as writer:
    df_acte.to_excel(writer, sheet_name='Acte Legislative', index=False)
    df_art.to_excel(writer, sheet_name='Articole', index=False)
    df_dom.to_excel(writer, sheet_name='Domenii', index=False)
    df_acte_dom.to_excel(writer, sheet_name='Acte-Domenii', index=False)
    df_art_dom.to_excel(writer, sheet_name='Articole-Domenii', index=False)
    df_issues.to_excel(writer, sheet_name='Issues', index=False)
    df_art_issues.to_excel(writer, sheet_name='Articole-Issues', index=False)
    df_acte_issues.to_excel(writer, sheet_name='Acte-Issues', index=False)
    df_struct_issues.to_excel(writer, sheet_name='Structure-Issues', index=False)

print(f'\n✓ All Excel files created!')
print(f'✓ Summary workbook: {summary_file.name}')

# Clean up CSV files
print('\nCleaning up temporary CSV files...')
for csv_file in export_dir.glob(f'*_local_{timestamp}.csv'):
    csv_file.unlink()
    
print('Done!')
"@

Write-Host "`n=== Export Complete ===" -ForegroundColor Green
Write-Host "Files saved to: $exportDir" -ForegroundColor Green
Write-Host "`nTo compare with VPS, run: .\scripts\export_vps_to_excel.ps1" -ForegroundColor Yellow
Write-Host ""

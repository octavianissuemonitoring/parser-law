"""
Export database tables to Excel files.
"""
import pandas as pd
import psycopg2
from datetime import datetime
import os
from pathlib import Path

def export_db_to_excel(host='localhost', port=5432, database='monitoring_platform', 
                       user='legislatie_user', password='legislatie_pass'):
    """Export all main tables to Excel format."""
    
    # Create export directory
    export_dir = Path(__file__).parent.parent / 'data' / 'export'
    export_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        print(f"Connected to database: {database}")
        
        # Export acte_legislative
        print("\nExporting acte_legislative...")
        df_acte = pd.read_sql("""
            SELECT 
                id, tip_act, nr_act, data_act, an_act, titlu_act, 
                emitent_act, mof_nr, mof_data, mof_an, 
                ai_status, ai_processed_at, export_status,
                versiune, created_at, updated_at
            FROM legislatie.acte_legislative 
            ORDER BY id
        """, conn)
        
        output_file = export_dir / f'acte_legislative_{timestamp}.xlsx'
        df_acte.to_excel(output_file, index=False, engine='openpyxl')
        print(f"✓ Exported {len(df_acte)} acte legislative to {output_file.name}")
        
        # Export articole (limited to prevent huge files)
        print("\nExporting articole...")
        df_art = pd.read_sql("""
            SELECT 
                id, act_id, articol_nr, articol_label,
                titlu_nr, titlu_denumire, capitol_nr, capitol_denumire,
                sectiune_nr, sectiune_denumire, subsectiune_nr,
                alineat_nr, litera_nr, text_articol,
                ai_status, ai_processed_at,
                versiune, created_at
            FROM legislatie.articole 
            ORDER BY act_id, id 
            LIMIT 10000
        """, conn)
        
        output_file = export_dir / f'articole_{timestamp}.xlsx'
        df_art.to_excel(output_file, index=False, engine='openpyxl')
        print(f"✓ Exported {len(df_art)} articole to {output_file.name}")
        
        # Export domenii
        print("\nExporting domenii...")
        df_dom = pd.read_sql("""
            SELECT id, nume, cod, descriere, activ, created_at, updated_at
            FROM legislatie.domenii 
            ORDER BY id
        """, conn)
        
        output_file = export_dir / f'domenii_{timestamp}.xlsx'
        df_dom.to_excel(output_file, index=False, engine='openpyxl')
        print(f"✓ Exported {len(df_dom)} domenii to {output_file.name}")
        
        # Export acte_domenii relationships
        print("\nExporting acte_domenii...")
        df_acte_dom = pd.read_sql("""
            SELECT 
                ad.id, ad.act_id, ad.domeniu_id,
                al.titlu_act as act_titlu,
                d.nume as domeniu_nume, d.cod as domeniu_cod,
                ad.created_at
            FROM legislatie.acte_domenii ad
            JOIN legislatie.acte_legislative al ON ad.act_id = al.id
            JOIN legislatie.domenii d ON ad.domeniu_id = d.id
            ORDER BY ad.id
        """, conn)
        
        output_file = export_dir / f'acte_domenii_{timestamp}.xlsx'
        df_acte_dom.to_excel(output_file, index=False, engine='openpyxl')
        print(f"✓ Exported {len(df_acte_dom)} acte-domenii links to {output_file.name}")
        
        # Export articole_domenii relationships
        print("\nExporting articole_domenii...")
        df_art_dom = pd.read_sql("""
            SELECT 
                ad.id, ad.articol_id, ad.domeniu_id,
                art.articol_nr, art.act_id,
                d.nume as domeniu_nume, d.cod as domeniu_cod,
                ad.created_at
            FROM legislatie.articole_domenii ad
            JOIN legislatie.articole art ON ad.articol_id = art.id
            JOIN legislatie.domenii d ON ad.domeniu_id = d.id
            ORDER BY ad.id
        """, conn)
        
        output_file = export_dir / f'articole_domenii_{timestamp}.xlsx'
        df_art_dom.to_excel(output_file, index=False, engine='openpyxl')
        print(f"✓ Exported {len(df_art_dom)} articole-domenii links to {output_file.name}")
        
        # Create summary file with all tables in one workbook
        print("\nCreating summary workbook...")
        summary_file = export_dir / f'database_export_all_{timestamp}.xlsx'
        with pd.ExcelWriter(summary_file, engine='openpyxl') as writer:
            df_acte.to_excel(writer, sheet_name='Acte Legislative', index=False)
            df_art.to_excel(writer, sheet_name='Articole', index=False)
            df_dom.to_excel(writer, sheet_name='Domenii', index=False)
            df_acte_dom.to_excel(writer, sheet_name='Acte-Domenii', index=False)
            df_art_dom.to_excel(writer, sheet_name='Articole-Domenii', index=False)
        
        print(f"✓ Created summary workbook: {summary_file.name}")
        
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"Export completed successfully!")
        print(f"Files saved to: {export_dir}")
        print(f"{'='*60}")
        
        return export_dir
        
    except Exception as e:
        print(f"\n❌ Error during export: {e}")
        print("\nMake sure you have installed required packages:")
        print("  pip install pandas openpyxl psycopg2-binary")
        raise


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        # Allow connecting to VPS
        # Usage: python export_to_excel.py 109.123.249.228 5432 monitoring_platform user pass
        host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 5432
        database = sys.argv[3] if len(sys.argv) > 3 else 'monitoring_platform'
        user = sys.argv[4] if len(sys.argv) > 4 else 'legislatie_user'
        password = sys.argv[5] if len(sys.argv) > 5 else 'legislatie_pass'
        
        export_db_to_excel(host, port, database, user, password)
    else:
        # Use local DB by default
        export_db_to_excel()

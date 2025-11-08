#!/usr/bin/env python3
"""
Cleanup script pentru fișiere vechi din rezultate/.
Menține doar cel mai recent fișier per act.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import argparse


def parse_filename(filename: str):
    """
    Parse filename: LEGE_123_2024_20251107_211711.csv
    Returns: (act_name, timestamp)
    """
    match = re.match(r'(.+?)_(\d{8}_\d{6})\.(csv|md)', filename)
    if match:
        act_name = match.group(1)
        timestamp_str = match.group(2)
        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        return act_name, timestamp
    return None, None


def find_duplicates(rezultate_dir: Path):
    """Găsește fișiere duplicate (același act, timestamp diferit)."""
    acts = defaultdict(list)
    
    for csv_file in rezultate_dir.glob("*.csv"):
        act_name, timestamp = parse_filename(csv_file.name)
        if act_name and timestamp:
            acts[act_name].append((csv_file, timestamp))
    
    duplicates = {}
    for act_name, files in acts.items():
        if len(files) > 1:
            # Sort by timestamp (newest first)
            files.sort(key=lambda x: x[1], reverse=True)
            duplicates[act_name] = files
    
    return duplicates


def cleanup_duplicates(rezultate_dir: Path, dry_run: bool = True, quiet: bool = False):
    """Șterge duplicate, păstrând doar cel mai recent."""
    duplicates = find_duplicates(rezultate_dir)
    
    if not duplicates:
        if not quiet:
            print("✅ No duplicates found")
        return 0
    
    if not quiet:
        print(f"📊 Found {len(duplicates)} acts with duplicates\n")
    
    total_deleted = 0
    for act_name, files in duplicates.items():
        latest_file, latest_time = files[0]
        old_files = files[1:]
        
        if not quiet:
            print(f"📄 {act_name}")
            print(f"   ✅ KEEP:   {latest_file.name} ({latest_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        for old_file, old_time in old_files:
            age_days = (datetime.now() - old_time).days
            if not quiet:
                print(f"   ❌ DELETE: {old_file.name} ({age_days} days old)")
            
            if not dry_run:
                # Delete CSV
                old_file.unlink()
                total_deleted += 1
                
                # Delete MD
                md_file = old_file.with_suffix('.md')
                if md_file.exists():
                    md_file.unlink()
                    total_deleted += 1
        
        if not quiet:
            print()
    
    if dry_run:
        expected_delete = sum(len(files) - 1 for files in duplicates.values()) * 2
        if not quiet:
            print(f"🔍 DRY RUN: Would delete {expected_delete} files")
            print("   Run with --execute to actually delete")
        return 0
    else:
        if not quiet:
            print(f"✅ Deleted {total_deleted} files")
        else:
            print(f"Deleted {total_deleted} files")
        return total_deleted


def get_stats(rezultate_dir: Path):
    """Afișează statistici despre fișiere."""
    csv_files = list(rezultate_dir.glob("*.csv"))
    md_files = list(rezultate_dir.glob("*.md"))
    
    total_size = sum(f.stat().st_size for f in csv_files + md_files)
    
    print("="*70)
    print("📊 Storage Statistics")
    print("="*70)
    print(f"Total files:    {len(csv_files)} CSV + {len(md_files)} MD = {len(csv_files) + len(md_files)}")
    print(f"Total size:     {total_size / 1024:.2f} KB ({total_size / 1024 / 1024:.2f} MB)")
    
    if csv_files:
        avg_size = total_size / len(csv_files + md_files)
        print(f"Average size:   {avg_size / 1024:.2f} KB per file")
    
    print("="*70)
    
    # Duplicates
    duplicates = find_duplicates(rezultate_dir)
    if duplicates:
        duplicate_count = sum(len(files) - 1 for files in duplicates.values())
        duplicate_size = 0
        
        for act_name, files in duplicates.items():
            for old_file, _ in files[1:]:
                duplicate_size += old_file.stat().st_size
                md_file = old_file.with_suffix('.md')
                if md_file.exists():
                    duplicate_size += md_file.stat().st_size
        
        print(f"\n⚠️  Found {duplicate_count} acts with duplicates")
        print(f"   Total duplicate files: {duplicate_count * 2} (CSV + MD)")
        print(f"   Wasted space: {duplicate_size / 1024:.2f} KB ({duplicate_size / 1024 / 1024:.2f} MB)")
        print(f"   Potential savings: {duplicate_size / total_size * 100:.1f}%")
    else:
        print(f"\n✅ No duplicates found - optimal storage")


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup fișiere vechi din rezultate/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemple:

  # Vezi statistici (safe, nu modifică nimic)
  python cleanup_files.py --stats

  # Vezi ce ar șterge (dry run)
  python cleanup_files.py

  # Șterge duplicate efectiv
  python cleanup_files.py --execute

  # Quiet mode (doar rezultat final)
  python cleanup_files.py --execute --quiet
        """
    )
    
    parser.add_argument(
        '--rezultate-dir',
        default='rezultate',
        help='Director rezultate (default: rezultate)'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Afișează doar statistici (no cleanup)'
    )
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execută cleanup (fără --execute e doar preview)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress detailed output'
    )
    
    args = parser.parse_args()
    
    rezultate_dir = Path(args.rezultate_dir)
    
    if not rezultate_dir.exists():
        print(f"❌ Directory not found: {rezultate_dir}")
        return 1
    
    # Stats only
    if args.stats:
        get_stats(rezultate_dir)
        return 0
    
    dry_run = not args.execute
    
    if dry_run and not args.quiet:
        print("🔍 DRY RUN MODE - No files will be deleted")
        print("   Use --execute to actually perform cleanup\n")
    
    # Cleanup duplicates
    deleted = cleanup_duplicates(rezultate_dir, dry_run, args.quiet)
    
    if not dry_run and not args.quiet:
        print("\n" + "="*70)
        get_stats(rezultate_dir)
    
    return 0


if __name__ == "__main__":
    exit(main())

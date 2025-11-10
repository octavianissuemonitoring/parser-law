"""
Import Service - Import CSV and Markdown files into database with change tracking.
"""
import os
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ActLegislativ, Articol, ActeModificari, ArticoleModificari
from app.database import async_sessionmaker
from app.services.diff_service import ArticleDiffService


class ImportService:
    """Service for importing legislative acts and articles from CSV/MD files."""
    
    def __init__(self, rezultate_dir: str = "/app/rezultate"):
        """
        Initialize import service.
        
        Args:
            rezultate_dir: Path to directory containing CSV and MD files
        """
        self.rezultate_dir = Path(rezultate_dir)
        
    async def import_all_files(self, db: AsyncSession) -> Dict[str, any]:
        """
        Import all CSV files from rezultate directory.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with import statistics
        """
        if not self.rezultate_dir.exists():
            return {
                "success": False,
                "error": f"Directory {self.rezultate_dir} does not exist",
                "imported_acts": 0,
                "imported_articles": 0,
            }
        
        # Find all CSV files
        csv_files = list(self.rezultate_dir.glob("*.csv"))
        
        if not csv_files:
            return {
                "success": False,
                "error": "No CSV files found in rezultate directory",
                "imported_acts": 0,
                "imported_articles": 0,
            }
        
        print(f"📁 Found {len(csv_files)} CSV files")
        
        stats = {
            "success": True,
            "total_files": len(csv_files),
            "imported_acts": 0,
            "updated_acts": 0,
            "imported_articles": 0,
            "skipped_acts": 0,
            "errors": [],
        }
        
        for csv_file in csv_files:
            try:
                print(f"\n🔄 Processing: {csv_file.name}")
                result = await self.import_csv_file(csv_file, db)
                
                if result["success"]:
                    if result.get("updated"):
                        stats["updated_acts"] += 1
                        stats["imported_articles"] += result["articles_count"]
                        print(f"🔄 Updated: {result['act_title']}")
                        print(f"   📊 {result['articles_count']} articles (was {result.get('old_articles_count', 0)})")
                    else:
                        stats["imported_acts"] += 1
                        stats["imported_articles"] += result["articles_count"]
                        print(f"✅ Imported: {result['act_title']}")
                        print(f"   📊 {result['articles_count']} articles")
                else:
                    if result.get("skipped"):
                        stats["skipped_acts"] += 1
                        print(f"⏭️  Skipped: {result.get('reason', 'Unknown')}")
                    else:
                        stats["errors"].append({
                            "file": csv_file.name,
                            "error": result.get("error", "Unknown error"),
                        })
                        print(f"❌ Error: {result.get('error')}")
                        
            except Exception as e:
                stats["errors"].append({
                    "file": csv_file.name,
                    "error": str(e),
                })
                print(f"❌ Exception: {str(e)}")
        
        print(f"\n{'='*60}")
        print(f"📈 Import Summary:")
        print(f"   ✅ New acts: {stats['imported_acts']}")
        print(f"   🔄 Updated acts: {stats['updated_acts']}")
        print(f"   📊 Total articles: {stats['imported_articles']}")
        print(f"   ⏭️  Skipped acts: {stats['skipped_acts']}")
        print(f"   ❌ Errors: {len(stats['errors'])}")
        print(f"{'='*60}")
        
        # Cleanup old files after successful import
        if stats["imported_acts"] > 0 or stats["updated_acts"] > 0:
            self._cleanup_old_files()
        
        return stats
    
    async def import_csv_file(
        self,
        csv_file: Path,
        db: AsyncSession,
    ) -> Dict[str, any]:
        """
        Import a single CSV file with its articles.
        
        Args:
            csv_file: Path to CSV file
            db: Database session
            
        Returns:
            Dictionary with import result
        """
        try:
            # Read CSV file
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                return {
                    "success": False,
                    "error": "CSV file is empty",
                }
            
            # Extract act data from first row
            first_row = rows[0]
            act_data = self._extract_act_data(first_row, csv_file)
            
            # Check if act already exists by URL
            query = select(ActLegislativ).where(
                ActLegislativ.url_legislatie == act_data["url_legislatie"]
            ).options(selectinload(ActLegislativ.articole))
            result = await db.execute(query)
            existing_act = result.scalar_one_or_none()
            
            # Read corresponding MD file for HTML content
            md_file = csv_file.with_suffix('.md')
            html_content = None
            if md_file.exists():
                with open(md_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            
            # Parse new articles data
            new_articles_data = []
            for idx, row in enumerate(rows, start=1):
                article_data = self._extract_article_data(row, None, idx)
                if article_data:
                    new_articles_data.append(article_data)
            
            if existing_act:
                # ===== UPDATE EXISTING ACT WITH DIFF TRACKING =====
                print(f"   🔄 Updating existing act (ID: {existing_act.id}, v{existing_act.versiune})...")
                
                # Calculate diff between old and new articles
                old_articles = existing_act.articole
                diff = ArticleDiffService.calculate_diff(old_articles, new_articles_data)
                summary = ArticleDiffService.get_relabeling_summary(diff)
                
                print(f"   📊 Diff: +{summary['added']} ~{summary['modified']} -{summary['deleted']} ={summary['unchanged']}")
                
                # Increment version
                existing_act.versiune += 1
                new_version = existing_act.versiune
                
                # Create modification record
                modificare = ActeModificari(
                    act_id=existing_act.id,
                    versiune=new_version,
                    tip_modificare='update_partial' if summary['total_changes'] < len(old_articles) else 'update_full',
                    sursa_modificare=act_data.get("url_legislatie"),
                    modificat_de='import_service',
                    articole_noi=summary['added'],
                    articole_modificate=summary['modified'],
                    articole_sterse=summary['deleted'],
                    total_articole=len(new_articles_data)
                )
                db.add(modificare)
                await db.flush()  # Get modificare.id
                
                # Track article changes
                # 1. Handle deleted articles
                for deleted_info in diff['deleted']:
                    art_change = ArticoleModificari(
                        modificare_id=modificare.id,
                        articol_id=deleted_info['articol_id'],
                        articol_nr=deleted_info['articol_nr'],
                        articol_label=deleted_info['articol_label'],
                        ordine=deleted_info['ordine'],
                        tip_schimbare='deleted',
                        text_vechi=deleted_info['text_vechi'],
                        issue_vechi=deleted_info.get('issue_vechi'),
                        explicatie_veche=deleted_info.get('explicatie_veche'),
                        necesita_reetichetare=False,  # Deleted don't need re-labeling
                    )
                    db.add(art_change)
                
                # 2. Delete old articles from DB
                await db.execute(delete(Articol).where(Articol.act_id == existing_act.id))
                
                # 3. Insert new articles and track changes
                article_id_map = {}  # Map ordine -> new article_id
                
                for art_data in new_articles_data:
                    art_data['act_id'] = existing_act.id
                    new_article = Articol(**art_data)
                    db.add(new_article)
                    await db.flush()  # Get new article.id
                    
                    if art_data.get('ordine'):
                        article_id_map[art_data['ordine']] = new_article.id
                
                # 4. Track modified articles
                for modified_info in diff['modified']:
                    # Find new article_id
                    new_art_id = article_id_map.get(modified_info['ordine'])
                    
                    art_change = ArticoleModificari(
                        modificare_id=modificare.id,
                        articol_id=new_art_id,
                        articol_nr=modified_info['articol_nr'],
                        articol_label=modified_info['articol_label'],
                        ordine=modified_info['ordine'],
                        tip_schimbare='modified',
                        text_vechi=modified_info['text_vechi'],
                        text_nou=modified_info['text_nou'],
                        issue_vechi=modified_info.get('issue_vechi'),
                        explicatie_veche=modified_info.get('explicatie_veche'),
                        necesita_reetichetare=True,
                    )
                    db.add(art_change)
                
                # 5. Track added articles
                for added_info in diff['added']:
                    new_art_id = article_id_map.get(added_info['ordine'])
                    
                    art_change = ArticoleModificari(
                        modificare_id=modificare.id,
                        articol_id=new_art_id,
                        articol_nr=added_info['articol_nr'],
                        articol_label=added_info['articol_label'],
                        ordine=added_info['ordine'],
                        tip_schimbare='added',
                        text_nou=added_info['text_nou'],
                        necesita_reetichetare=True,
                    )
                    db.add(art_change)
                
                # Update act metadata
                for key, value in act_data.items():
                    if key not in ['id', 'versiune']:
                        setattr(existing_act, key, value)
                
                if html_content:
                    existing_act.html_content = html_content
                
                await db.commit()
                
                print(f"   ✅ Updated to v{new_version}")
                print(f"   🏷️  {summary['needs_relabeling']} articles need re-labeling")
                
                return {
                    "success": True,
                    "updated": True,
                    "act_id": existing_act.id,
                    "act_title": existing_act.titlu_act,
                    "versiune": new_version,
                    "articles_count": len(new_articles_data),
                    "old_articles_count": len(old_articles),
                    "diff": summary,
                }
            
            # ===== CREATE NEW ACT =====
            new_act = ActLegislativ(**act_data, versiune=1)
            db.add(new_act)
            await db.flush()  # Get act.id without committing
            
            if html_content:
                new_act.html_content = html_content
            
            # Create initial modification record
            modificare = ActeModificari(
                act_id=new_act.id,
                versiune=1,
                tip_modificare='initial',
                sursa_modificare=act_data.get("url_legislatie"),
                modificat_de='import_service',
                articole_noi=len(new_articles_data),
                articole_modificate=0,
                articole_sterse=0,
                total_articole=len(new_articles_data)
            )
            db.add(modificare)
            await db.flush()
            
            # Import articles and track as new
            for art_data in new_articles_data:
                art_data['act_id'] = new_act.id
                article = Articol(**art_data)
                db.add(article)
                await db.flush()
                
                # Track as added
                art_change = ArticoleModificari(
                    modificare_id=modificare.id,
                    articol_id=article.id,
                    articol_nr=art_data.get('articol_nr'),
                    articol_label=art_data.get('articol_label'),
                    ordine=art_data.get('ordine'),
                    tip_schimbare='added',
                    text_nou=art_data.get('text_articol'),
                    necesita_reetichetare=True,
                )
                db.add(art_change)
            
            await db.commit()
            
            return {
                "success": True,
                "updated": False,
                "act_id": new_act.id,
                "act_title": new_act.titlu_act,
                "versiune": 1,
                "articles_count": len(new_articles_data),
                "needs_relabeling": len(new_articles_data),
            }
            
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "error": str(e),
            }
    
    def _extract_act_data(self, row: Dict[str, str], csv_file: Path) -> Dict[str, any]:
        """Extract ActLegislativ data from CSV row."""
        
        # Parse dates
        data_act = self._parse_date(row.get('data_act') or row.get('Data'))
        mof_data = self._parse_date(row.get('mof_data'))
        
        # Generate URL from filename (will be replaced with actual URL if available)
        url_base = "https://legislatie.just.ro/Public/FormaPrintabila/"
        url_legislatie = url_base + csv_file.stem
        
        return {
            "tip_act": row.get('tip_act', '').strip(),
            "nr_act": row.get('nr_act', '').strip(),
            "data_act": data_act,
            "an_act": self._parse_int(row.get('an_act') or row.get('An')),
            "titlu_act": row.get('titlu_act') or row.get('Titlu_Act', ''),
            "emitent_act": row.get('emitent_act', '').strip() or None,
            "mof_nr": row.get('mof_nr', '').strip() or None,
            "mof_data": mof_data,
            "mof_an": self._parse_int(row.get('mof_an')),
            "url_legislatie": url_legislatie,
            "confidence_score": self._parse_float(row.get('confidence_score')),
        }
    
    def _extract_article_data(
        self,
        row: Dict[str, str],
        act_id: Optional[int],
        ordine: int,
    ) -> Optional[Dict[str, any]]:
        """Extract Articol data from CSV row."""
        
        # Check if row has actual article content
        text_articol = row.get('text_articol', '').strip()
        if not text_articol:
            return None
        
        data = {
            "ordine": ordine,
            "articol_nr": row.get('Articol_Nr', '').strip() or None,
            "articol_label": row.get('articol_label', '').strip() or None,
            "titlu_nr": self._parse_int(row.get('titlu_nr')),
            "titlu_denumire": row.get('Titlu_Den', '').strip() or None,
            "capitol_nr": self._parse_int(row.get('capitol_nr')),
            "capitol_denumire": row.get('Capitol_Den', '').strip() or None,
            "sectiune_nr": self._parse_int(row.get('sectiune_nr')),
            "sectiune_denumire": row.get('Sectiune_Den', '').strip() or None,
            "subsectiune_nr": self._parse_int(row.get('subsectiune_nr')),
            "subsectiune_denumire": row.get('Subsectiune_Den', '').strip() or None,
            "text_articol": text_articol,
            "issue": row.get('issue', '').strip() or None,
            "explicatie": row.get('explicatie', '').strip() or None,
        }
        
        # Only add act_id if provided
        if act_id is not None:
            data["act_id"] = act_id
        
        return data
    
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string in DD/MM/YYYY format."""
        if not date_str or not date_str.strip():
            return None
        
        try:
            # Try DD/MM/YYYY format
            return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
        except ValueError:
            try:
                # Try YYYY-MM-DD format
                return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
            except ValueError:
                return None
    
    @staticmethod
    def _parse_int(value: Optional[str]) -> Optional[int]:
        """Parse integer from string."""
        if not value or not str(value).strip():
            return None
        try:
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _parse_float(value: Optional[str]) -> Optional[float]:
        """Parse float from string."""
        if not value or not str(value).strip():
            return None
        try:
            return float(str(value).strip())
        except (ValueError, TypeError):
            return None
    
    def _cleanup_old_files(self):
        """
        Cleanup automat: păstrează doar cel mai recent fișier per act.
        Șterge duplicate mai vechi după import cu succes.
        """
        from collections import defaultdict
        import re
        
        try:
            # Group files by act name
            acts_by_name = defaultdict(list)
            
            for csv_file in self.rezultate_dir.glob("*.csv"):
                # Parse: LEGE_123_2024_20251107_211711.csv
                match = re.match(r'(.+?)_(\d{8}_\d{6})\.csv', csv_file.name)
                if match:
                    act_name = match.group(1)
                    timestamp = match.group(2)
                    acts_by_name[act_name].append((csv_file, timestamp))
            
            # Keep only latest per act
            deleted_count = 0
            for act_name, files in acts_by_name.items():
                if len(files) > 1:
                    # Sort by timestamp (newest first)
                    files.sort(key=lambda x: x[1], reverse=True)
                    latest = files[0][0]
                    
                    # Delete older files
                    for old_file, _ in files[1:]:
                        print(f"   🗑️  Cleanup: {old_file.name}")
                        old_file.unlink()
                        deleted_count += 1
                        
                        # Delete corresponding .md
                        md_file = old_file.with_suffix('.md')
                        if md_file.exists():
                            md_file.unlink()
                            deleted_count += 1
            
            if deleted_count > 0:
                print(f"   ✅ Cleaned up {deleted_count} old files")
        
        except Exception as e:
            print(f"   ⚠️  Cleanup warning: {e}")


async def run_import(rezultate_dir: str = "/app/rezultate") -> Dict[str, any]:
    """
    Run import from command line or script.
    
    Args:
        rezultate_dir: Path to directory containing CSV and MD files
        
    Returns:
        Dictionary with import statistics
    """
    print("\n" + "="*60)
    print("🚀 Import Service - Legislative Acts & Articles")
    print("="*60 + "\n")
    
    service = ImportService(rezultate_dir)
    
    async with async_sessionmaker() as db:
        stats = await service.import_all_files(db)
    
    return stats


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_import())

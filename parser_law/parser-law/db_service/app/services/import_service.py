"""
Import Service - Import CSV and Markdown files into database.
"""
import os
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActLegislativ, Articol
from app.database import async_sessionmaker


class ImportService:
    """Service for importing legislative acts and articles from CSV/MD files."""
    
    def __init__(self, rezultate_dir: str = "../rezultate"):
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
            "imported_articles": 0,
            "skipped_acts": 0,
            "errors": [],
        }
        
        for csv_file in csv_files:
            try:
                print(f"\n🔄 Processing: {csv_file.name}")
                result = await self.import_csv_file(csv_file, db)
                
                if result["success"]:
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
        print(f"   ✅ Imported acts: {stats['imported_acts']}/{stats['total_files']}")
        print(f"   📊 Total articles: {stats['imported_articles']}")
        print(f"   ⏭️  Skipped acts: {stats['skipped_acts']}")
        print(f"   ❌ Errors: {len(stats['errors'])}")
        print(f"{'='*60}")
        
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
            )
            result = await db.execute(query)
            existing_act = result.scalar_one_or_none()
            
            if existing_act:
                return {
                    "success": False,
                    "skipped": True,
                    "reason": f"Act already exists (ID: {existing_act.id})",
                    "act_id": existing_act.id,
                }
            
            # Create new act
            new_act = ActLegislativ(**act_data)
            db.add(new_act)
            await db.flush()  # Get act.id without committing
            
            # Read corresponding MD file for HTML content
            md_file = csv_file.with_suffix('.md')
            if md_file.exists():
                with open(md_file, 'r', encoding='utf-8') as f:
                    new_act.html_content = f.read()
            
            # Import articles
            articles_imported = 0
            for idx, row in enumerate(rows, start=1):
                article_data = self._extract_article_data(row, new_act.id, idx)
                if article_data:  # Only create if there's actual content
                    article = Articol(**article_data)
                    db.add(article)
                    articles_imported += 1
            
            await db.commit()
            
            return {
                "success": True,
                "act_id": new_act.id,
                "act_title": new_act.titlu_act,
                "articles_count": articles_imported,
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
        act_id: int,
        ordine: int,
    ) -> Optional[Dict[str, any]]:
        """Extract Articol data from CSV row."""
        
        # Check if row has actual article content
        text_articol = row.get('text_articol', '').strip()
        if not text_articol:
            return None
        
        return {
            "act_id": act_id,
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


async def run_import(rezultate_dir: str = "../rezultate") -> Dict[str, any]:
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

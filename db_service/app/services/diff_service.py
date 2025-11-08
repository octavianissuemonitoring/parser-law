"""
Diff Service - Calculate differences between article versions for re-labeling.
"""
from typing import Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher

from app.models import Articol


class ArticleDiffService:
    """
    Service for calculating diffs between old and new article versions.
    Used to determine which articles need LLM re-labeling.
    """
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        return SequenceMatcher(None, text1, text2).ratio()
    
    @staticmethod
    def is_significant_change(old_text: str, new_text: str, threshold: float = 0.95) -> bool:
        """
        Determine if text change is significant enough for re-labeling.
        
        Args:
            old_text: Original text
            new_text: New text
            threshold: Similarity threshold (changes below this are significant)
            
        Returns:
            True if change is significant
        """
        if old_text == new_text:
            return False
        
        similarity = ArticleDiffService.calculate_similarity(old_text, new_text)
        return similarity < threshold
    
    @staticmethod
    def calculate_diff(
        old_articles: List[Articol],
        new_articles_data: List[Dict],
        similarity_threshold: float = 0.95
    ) -> Dict[str, List[Dict]]:
        """
        Calculate comprehensive diff between old and new article versions.
        
        Args:
            old_articles: List of existing Articol objects from DB
            new_articles_data: List of dicts with new article data
            similarity_threshold: Threshold for detecting significant changes
            
        Returns:
            Dict with keys: 'added', 'modified', 'deleted', 'unchanged'
            Each containing list of article diffs
        """
        
        # Build lookup dictionaries
        old_by_nr: Dict[str, Articol] = {}
        old_by_ordine: Dict[int, Articol] = {}
        
        for art in old_articles:
            if art.articol_nr:
                old_by_nr[art.articol_nr] = art
            if art.ordine:
                old_by_ordine[art.ordine] = art
        
        new_by_nr: Dict[str, Dict] = {}
        new_by_ordine: Dict[int, Dict] = {}
        
        for art_data in new_articles_data:
            if art_data.get('articol_nr'):
                new_by_nr[art_data['articol_nr']] = art_data
            if art_data.get('ordine'):
                new_by_ordine[art_data['ordine']] = art_data
        
        # Calculate diff
        result = {
            'added': [],
            'modified': [],
            'deleted': [],
            'unchanged': []
        }
        
        # Track processed articles
        processed_old: Set[int] = set()
        processed_new: Set[str] = set()  # Use articol_nr as key
        
        # 1. Find modified and unchanged (match by articol_nr first, then ordine)
        for art_nr, old_art in old_by_nr.items():
            if art_nr in new_by_nr:
                new_data = new_by_nr[art_nr]
                processed_old.add(old_art.id)
                processed_new.add(art_nr)
                
                # Check if text changed
                old_text = old_art.text_articol or ""
                new_text = new_data.get('text_articol', "")
                
                if ArticleDiffService.is_significant_change(old_text, new_text, similarity_threshold):
                    result['modified'].append({
                        'articol_id': old_art.id,
                        'articol_nr': art_nr,
                        'articol_label': old_art.articol_label,
                        'ordine': old_art.ordine,
                        'text_vechi': old_text,
                        'text_nou': new_text,
                        'issue_vechi': old_art.issue,
                        'explicatie_veche': old_art.explicatie,
                        'similarity': ArticleDiffService.calculate_similarity(old_text, new_text),
                    })
                else:
                    result['unchanged'].append({
                        'articol_id': old_art.id,
                        'articol_nr': art_nr,
                        'articol_label': old_art.articol_label,
                        'ordine': old_art.ordine,
                    })
        
        # 2. Match by ordine for articles without articol_nr
        for ordine, old_art in old_by_ordine.items():
            if old_art.id in processed_old:
                continue
            
            if ordine in new_by_ordine:
                new_data = new_by_ordine[ordine]
                new_nr = new_data.get('articol_nr', '')
                
                if new_nr in processed_new:
                    continue
                
                processed_old.add(old_art.id)
                if new_nr:
                    processed_new.add(new_nr)
                
                old_text = old_art.text_articol or ""
                new_text = new_data.get('text_articol', "")
                
                if ArticleDiffService.is_significant_change(old_text, new_text, similarity_threshold):
                    result['modified'].append({
                        'articol_id': old_art.id,
                        'articol_nr': new_nr or old_art.articol_nr,
                        'articol_label': old_art.articol_label,
                        'ordine': ordine,
                        'text_vechi': old_text,
                        'text_nou': new_text,
                        'issue_vechi': old_art.issue,
                        'explicatie_veche': old_art.explicatie,
                        'similarity': ArticleDiffService.calculate_similarity(old_text, new_text),
                    })
                else:
                    result['unchanged'].append({
                        'articol_id': old_art.id,
                        'articol_nr': new_nr or old_art.articol_nr,
                        'articol_label': old_art.articol_label,
                        'ordine': ordine,
                    })
        
        # 3. Find deleted articles
        for old_art in old_articles:
            if old_art.id not in processed_old:
                result['deleted'].append({
                    'articol_id': old_art.id,
                    'articol_nr': old_art.articol_nr,
                    'articol_label': old_art.articol_label,
                    'ordine': old_art.ordine,
                    'text_vechi': old_art.text_articol,
                    'issue_vechi': old_art.issue,
                    'explicatie_veche': old_art.explicatie,
                })
        
        # 4. Find added articles
        for new_data in new_articles_data:
            new_nr = new_data.get('articol_nr', '')
            new_ordine = new_data.get('ordine')
            
            # Check if already processed
            already_processed = False
            if new_nr and new_nr in processed_new:
                already_processed = True
            elif new_ordine and new_ordine in new_by_ordine:
                # Check if this ordine was matched
                for processed_id in processed_old:
                    if old_by_ordine.get(new_ordine) and old_by_ordine[new_ordine].id == processed_id:
                        already_processed = True
                        break
            
            if not already_processed:
                result['added'].append({
                    'articol_id': None,  # Will be set after insert
                    'articol_nr': new_nr,
                    'articol_label': new_data.get('articol_label'),
                    'ordine': new_ordine,
                    'text_nou': new_data.get('text_articol', ''),
                })
        
        return result
    
    @staticmethod
    def get_relabeling_summary(diff: Dict[str, List[Dict]]) -> Dict[str, int]:
        """
        Generate summary statistics for re-labeling needs.
        
        Args:
            diff: Diff result from calculate_diff()
            
        Returns:
            Summary dict with counts
        """
        return {
            'total_changes': len(diff['added']) + len(diff['modified']) + len(diff['deleted']),
            'needs_relabeling': len(diff['added']) + len(diff['modified']),
            'added': len(diff['added']),
            'modified': len(diff['modified']),
            'deleted': len(diff['deleted']),
            'unchanged': len(diff['unchanged']),
        }

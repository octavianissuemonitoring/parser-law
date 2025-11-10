"""
Service for managing categories synced from Issue Monitoring.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)


class CategoryService:
    """Service for syncing and managing categories from Issue Monitoring."""
    
    def __init__(self):
        self.api_url = settings.issue_monitoring_api_url
        self.api_key = settings.issue_monitoring_api_key
        
        if not self.api_key:
            logger.warning("ISSUE_MONITORING_API_KEY not set - category sync will fail")
    
    async def fetch_categories_from_im(self) -> List[Dict]:
        """
        Fetch categories from Issue Monitoring API.
        
        Returns:
            List of category dicts from IM API
            
        Raises:
            Exception if API call fails
        """
        if not self.api_key:
            raise ValueError("ISSUE_MONITORING_API_KEY not configured")
        
        url = f"{self.api_url}/categories"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                logger.info(f"Fetching categories from {url}")
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                categories = response.json()
                logger.info(f"Fetched {len(categories)} categories from Issue Monitoring")
                
                return categories
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching categories: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Error fetching categories: {str(e)}")
                raise
    
    async def sync_categories(self, db: AsyncSession) -> Dict:
        """
        Sync categories from Issue Monitoring to local cache.
        
        Strategy:
        - Creates new categories
        - Updates existing categories (name, description, color, etc.)
        - Soft-deletes missing categories (is_active = false)
        - NEVER hard-deletes categories (preserves history)
        
        Returns:
            Dict with sync statistics
        """
        try:
            # Fetch from IM
            im_categories = await self.fetch_categories_from_im()
            
            stats = {
                "total_fetched": len(im_categories),
                "created": 0,
                "updated": 0,
                "deactivated": 0,
                "errors": 0,
                "synced_at": datetime.now().isoformat()
            }
            
            # Track which IM IDs we've seen
            im_category_ids = set()
            # Track which IM IDs we've seen
            im_category_ids = set()
            
            for cat in im_categories:
                try:
                    im_category_ids.add(cat["id"])
                    
                    # Check if category exists
                    query = text("""
                        SELECT id, name, description, color, icon, is_active
                        FROM legislatie.categories
                        WHERE im_category_id = :im_id
                    """)
                    result = await db.execute(query, {"im_id": cat["id"]})
                    existing = result.fetchone()
                    
                    if existing:
                        # Check if anything changed (to log meaningful updates)
                        changed = (
                            existing[1] != cat["name"] or
                            existing[2] != cat.get("description") or
                            existing[3] != cat.get("color") or
                            existing[4] != cat.get("icon") or
                            not existing[5]  # Was inactive, now active again
                        )
                        
                        if changed:
                            # Update existing
                            update_query = text("""
                                UPDATE legislatie.categories
                                SET name = :name,
                                    slug = :slug,
                                    description = :description,
                                    color = :color,
                                    icon = :icon,
                                    is_active = true,
                                    synced_at = NOW()
                                WHERE im_category_id = :im_id
                            """)
                            await db.execute(update_query, {
                                "im_id": cat["id"],
                                "name": cat["name"],
                                "slug": cat["slug"],
                                "description": cat.get("description"),
                                "color": cat.get("color"),
                                "icon": cat.get("icon")
                            })
                            stats["updated"] += 1
                            logger.info(f"Updated category: {cat['name']} (was: {existing[1]})")
                        else:
                            # Just touch synced_at
                            touch_query = text("""
                                UPDATE legislatie.categories
                                SET synced_at = NOW()
                                WHERE im_category_id = :im_id
                            """)
                            await db.execute(touch_query, {"im_id": cat["id"]})
                    else:
                        # Create new
                        insert_query = text("""
                            INSERT INTO legislatie.categories 
                                (im_category_id, name, slug, description, color, icon, is_active, synced_at)
                            VALUES 
                                (:im_id, :name, :slug, :description, :color, :icon, true, NOW())
                        """)
                        await db.execute(insert_query, {
                            "im_id": cat["id"],
                            "name": cat["name"],
                            "slug": cat["slug"],
                            "description": cat.get("description"),
                            "color": cat.get("color"),
                            "icon": cat.get("icon")
                        })
                        stats["created"] += 1
                        logger.info(f"Created category: {cat['name']}")
                        
                except Exception as e:
                    logger.error(f"Error syncing category {cat.get('name', 'unknown')}: {str(e)}")
                    stats["errors"] += 1
            
            # Deactivate categories that are no longer in IM
            # (except the default "Necategorizat" with im_category_id = 0)
            deactivate_query = text("""
                UPDATE legislatie.categories
                SET is_active = false, synced_at = NOW()
                WHERE im_category_id != 0 
                  AND im_category_id NOT IN :active_ids
                  AND is_active = true
                RETURNING name
            """)
            
            if im_category_ids:
                result = await db.execute(
                    deactivate_query,
                    {"active_ids": tuple(im_category_ids)}
                )
                deactivated = result.fetchall()
                stats["deactivated"] = len(deactivated)
                
                for row in deactivated:
                    logger.warning(f"Deactivated category (removed from IM): {row[0]}")
            
            await db.commit()
            
            logger.info(f"Category sync completed: {stats}")
            return stats
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Category sync failed: {str(e)}")
            raise
    
    async def get_local_categories(
        self,
        db: AsyncSession,
        active_only: bool = True
    ) -> List[Dict]:
        """
        Get categories from local cache.
        
        Args:
            db: Database session
            active_only: Return only active categories
            
        Returns:
            List of category dicts
        """
        query = text("""
            SELECT 
                id,
                im_category_id,
                name,
                slug,
                description,
                color,
                icon,
                ordine,
                is_active,
                synced_at
            FROM legislatie.categories
            WHERE (:active_only = false OR is_active = true)
            ORDER BY ordine ASC, name ASC
        """)
        
        result = await db.execute(query, {"active_only": active_only})
        rows = result.fetchall()
        
        return [
            {
                "id": row[0],
                "im_category_id": row[1],
                "name": row[2],
                "slug": row[3],
                "description": row[4],
                "color": row[5],
                "icon": row[6],
                "ordine": row[7],
                "is_active": row[8],
                "synced_at": row[9].isoformat() if row[9] else None
            }
            for row in rows
        ]
    
    async def add_categories_to_act(
        self,
        db: AsyncSession,
        act_id: int,
        category_ids: List[int],
        added_by: str = "system"
    ) -> Dict:
        """
        Add categories to a legislative act.
        
        Args:
            db: Database session
            act_id: Act ID
            category_ids: List of category IDs to add
            added_by: User/system adding categories
            
        Returns:
            Dict with operation results
        """
        stats = {"added": 0, "skipped": 0}
        
        for cat_id in category_ids:
            try:
                # Check if already exists
                check_query = text("""
                    SELECT 1 FROM legislatie.acte_categories
                    WHERE act_id = :act_id AND category_id = :cat_id
                """)
                result = await db.execute(check_query, {"act_id": act_id, "cat_id": cat_id})
                
                if result.fetchone():
                    stats["skipped"] += 1
                    continue
                
                # Insert
                insert_query = text("""
                    INSERT INTO legislatie.acte_categories (act_id, category_id, added_by)
                    VALUES (:act_id, :cat_id, :added_by)
                """)
                await db.execute(insert_query, {
                    "act_id": act_id,
                    "cat_id": cat_id,
                    "added_by": added_by
                })
                stats["added"] += 1
                
            except Exception as e:
                logger.error(f"Error adding category {cat_id} to act {act_id}: {str(e)}")
        
        await db.commit()
        return stats
    
    async def remove_categories_from_act(
        self,
        db: AsyncSession,
        act_id: int,
        category_ids: List[int]
    ) -> int:
        """
        Remove categories from a legislative act.
        
        Returns:
            Number of categories removed
        """
        if not category_ids:
            return 0
        
        query = text("""
            DELETE FROM legislatie.acte_categories
            WHERE act_id = :act_id AND category_id = ANY(:cat_ids)
        """)
        
        result = await db.execute(query, {
            "act_id": act_id,
            "cat_ids": category_ids
        })
        await db.commit()
        
        return result.rowcount
    
    async def get_act_categories(
        self,
        db: AsyncSession,
        act_id: int
    ) -> List[Dict]:
        """
        Get all categories assigned to an act.
        
        Returns:
            List of category dicts with metadata
        """
        query = text("""
            SELECT 
                c.id,
                c.im_category_id,
                c.name,
                c.slug,
                c.description,
                c.color,
                c.icon,
                ac.added_at,
                ac.added_by
            FROM legislatie.categories c
            JOIN legislatie.acte_categories ac ON c.id = ac.category_id
            WHERE ac.act_id = :act_id AND c.is_active = true
            ORDER BY c.ordine ASC, c.name ASC
        """)
        
        result = await db.execute(query, {"act_id": act_id})
        rows = result.fetchall()
        
        return [
            {
                "id": row[0],
                "im_category_id": row[1],
                "name": row[2],
                "slug": row[3],
                "description": row[4],
                "color": row[5],
                "icon": row[6],
                "added_at": row[7].isoformat() if row[7] else None,
                "added_by": row[8]
            }
            for row in rows
        ]

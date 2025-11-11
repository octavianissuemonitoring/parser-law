"""
Export Service - Send processed legislation to Issue Monitoring platform.

This service handles:
1. Building export packages from processed data
2. Sending data to Issue Monitoring API
3. Tracking export status and handling failures
4. Syncing updates for already exported items
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import httpx
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.act_legislativ import ActLegislativ
from app.models.articol import Articol
from app.models.anexa import Anexa
from app.models.issue import Issue

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting processed legislation to Issue Monitoring."""
    
    def __init__(self):
        """Initialize export service with API configuration."""
        self.api_url = os.getenv("ISSUE_MONITORING_API_URL", "https://api.issuemonitoring.ro/v1")
        self.api_key = os.getenv("ISSUE_MONITORING_API_KEY", "")
        
        if not self.api_key:
            logger.warning("ISSUE_MONITORING_API_KEY not set - exports will fail")
        
        # HTTP client configuration
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.retry_attempts = 3
        self.retry_delay = 2.0  # seconds
    
    async def build_export_package(
        self,
        session: AsyncSession,
        act_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Build export packages for acts ready to be sent to Issue Monitoring.
        
        Args:
            session: Database session
            act_id: Specific act ID to export (if None, exports pending acts)
            limit: Maximum number of acts to package
            
        Returns:
            List of export packages (one per act)
        """
        logger.info(f"Building export packages (act_id={act_id}, limit={limit})")
        
        # Query for acts ready to export
        query = select(ActLegislativ).options(
            selectinload(ActLegislativ.articole).selectinload(Articol.issues),
            selectinload(ActLegislativ.anexe).selectinload(Anexa.issues),
            selectinload(ActLegislativ.issues)
        )
        
        if act_id:
            query = query.where(ActLegislativ.id == act_id)
        else:
            # Only acts with AI processing completed and not yet exported
            query = query.where(
                and_(
                    ActLegislativ.ai_status == 'completed',
                    ActLegislativ.export_status.in_(['pending', 'error'])
                )
            ).limit(limit)
        
        result = await session.execute(query)
        acts = result.scalars().unique().all()
        
        packages = []
        for act in acts:
            try:
                package = await self._build_act_package(act)
                packages.append(package)
            except Exception as e:
                logger.error(f"Failed to build package for act {act.id}: {e}")
                # Mark as error but continue with other acts
                act.export_status = 'error'
                act.export_error = f"Package build failed: {str(e)}"
                await session.commit()
        
        logger.info(f"Built {len(packages)} export packages")
        return packages
    
    async def _build_act_package(self, act: ActLegislativ) -> Dict:
        """
        Build export package for a single act.
        
        Package structure:
        {
            "act": {...},           # Act metadata
            "articles": [...],      # Articles with issues
            "annexes": [...],       # Annexes with issues
            "issues": [...],        # All unique issues
            "metadata": {...}       # Export metadata
        }
        """
        # Collect all unique issues
        all_issues = set()
        
        # Add act-level issues
        for issue in act.issues:
            all_issues.add(issue)
        
        # Add article issues
        for articol in act.articole:
            for issue in articol.issues:
                all_issues.add(issue)
        
        # Add annex issues
        for anexa in act.anexe:
            for issue in anexa.issues:
                all_issues.add(issue)
        
        package = {
            "act": {
                "id": act.id,
                "nr_act": act.nr_act,
                "an_act": act.an_act,
                "titlu": act.titlu_act,
                "tip": act.tip,
                "emitent": act.emitent,
                "data_publicare": act.data_publicare.isoformat() if act.data_publicare else None,
                "link": act.link_legislatie,
                "metadata": act.metadate,
                "created_at": act.created_at.isoformat() if act.created_at else None
            },
            "articles": [
                {
                    "id": art.id,
                    "numar": art.numar_articol,
                    "titlu": art.titlu_articol,
                    "continut": art.continut,
                    "metadata": art.metadate,
                    "issue_ids": [issue.id for issue in art.issues]
                }
                for art in act.articole if art.ai_status == 'completed'
            ],
            "annexes": [
                {
                    "id": anex.id,
                    "numar": anex.anexa_nr,
                    "continut": anex.continut[:1000] if anex.continut else None,  # Truncate large content
                    "metadata": anex.metadate,
                    "issue_ids": [issue.id for issue in anex.issues]
                }
                for anex in act.anexe if anex.ai_status == 'completed'
            ],
            "issues": [
                {
                    "id": issue.id,
                    "denumire": issue.denumire,
                    "descriere": issue.descriere,
                    "source": issue.source,
                    "confidence_score": float(issue.confidence_score) if issue.confidence_score else None
                }
                for issue in all_issues
            ],
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "total_articles": len(act.articole),
                "processed_articles": len([a for a in act.articole if a.ai_status == 'completed']),
                "total_annexes": len(act.anexe),
                "processed_annexes": len([a for a in act.anexe if a.ai_status == 'completed']),
                "total_issues": len(all_issues)
            }
        }
        
        return package
    
    async def export_to_issue_monitoring(
        self,
        session: AsyncSession,
        act_id: Optional[int] = None,
        limit: int = 10
    ) -> Dict[str, int]:
        """
        Export processed acts to Issue Monitoring platform.
        
        Args:
            session: Database session
            act_id: Specific act ID to export (if None, exports pending)
            limit: Maximum number of acts to export
            
        Returns:
            Statistics: {"success": X, "error": Y, "skipped": Z}
        """
        logger.info(f"Starting export to Issue Monitoring (act_id={act_id}, limit={limit})")
        
        stats = {"success": 0, "error": 0, "skipped": 0}
        
        # Build export packages
        packages = await self.build_export_package(session, act_id, limit)
        
        if not packages:
            logger.info("No packages to export")
            return stats
        
        # Send each package to Issue Monitoring
        for package in packages:
            act_internal_id = package["act"]["id"]
            
            try:
                # Send to Issue Monitoring API
                success, im_id, error = await self._send_to_api(package)
                
                # Update act with export status
                stmt = select(ActLegislativ).where(ActLegislativ.id == act_internal_id)
                result = await session.execute(stmt)
                act = result.scalar_one_or_none()
                
                if not act:
                    logger.error(f"Act {act_internal_id} not found after export")
                    stats["error"] += 1
                    continue
                
                if success:
                    act.export_status = 'completed'
                    act.export_at = datetime.utcnow()
                    act.issue_monitoring_id = im_id
                    act.export_error = None
                    
                    # Update all associated articles and annexes
                    for articol in act.articole:
                        if articol.ai_status == 'completed':
                            articol.issue_monitoring_id = im_id
                    
                    for anexa in act.anexe:
                        if anexa.ai_status == 'completed':
                            anexa.issue_monitoring_id = im_id
                    
                    # Update all associated issues
                    for issue in package["issues"]:
                        stmt_issue = select(Issue).where(Issue.id == issue["id"])
                        result_issue = await session.execute(stmt_issue)
                        issue_obj = result_issue.scalar_one_or_none()
                        if issue_obj:
                            issue_obj.issue_monitoring_id = im_id
                    
                    await session.commit()
                    stats["success"] += 1
                    logger.info(f"✓ Exported act {act_internal_id} → Issue Monitoring ID: {im_id}")
                    
                else:
                    act.export_status = 'error'
                    act.export_error = error
                    await session.commit()
                    stats["error"] += 1
                    logger.error(f"✗ Failed to export act {act_internal_id}: {error}")
                
            except Exception as e:
                logger.error(f"Unexpected error exporting act {act_internal_id}: {e}")
                stats["error"] += 1
                
                # Try to mark as error in DB
                try:
                    stmt = select(ActLegislativ).where(ActLegislativ.id == act_internal_id)
                    result = await session.execute(stmt)
                    act = result.scalar_one_or_none()
                    if act:
                        act.export_status = 'error'
                        act.export_error = f"Unexpected error: {str(e)}"
                        await session.commit()
                except Exception as e2:
                    logger.error(f"Failed to update error status: {e2}")
        
        logger.info(f"Export completed: {stats}")
        return stats
    
    async def _send_to_api(self, package: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send export package to Issue Monitoring API with retry logic.
        
        Args:
            package: Export package to send
            
        Returns:
            Tuple of (success, issue_monitoring_id, error_message)
        """
        if not self.api_key:
            return False, None, "API key not configured"
        
        endpoint = f"{self.api_url}/legislation/import"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Parser-Law/1.0"
        }
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        endpoint,
                        json=package,
                        headers=headers
                    )
                    
                    if response.status_code == 200 or response.status_code == 201:
                        data = response.json()
                        im_id = data.get("id") or data.get("legislation_id")
                        logger.info(f"API success: {im_id}")
                        return True, im_id, None
                    
                    elif response.status_code == 409:
                        # Conflict - already exists
                        data = response.json()
                        im_id = data.get("existing_id")
                        logger.warning(f"Act already exists in Issue Monitoring: {im_id}")
                        return True, im_id, None
                    
                    elif response.status_code >= 500:
                        # Server error - retry
                        error_msg = f"Server error {response.status_code}: {response.text[:200]}"
                        logger.warning(f"Attempt {attempt}/{self.retry_attempts}: {error_msg}")
                        
                        if attempt < self.retry_attempts:
                            await asyncio.sleep(self.retry_delay * attempt)
                            continue
                        else:
                            return False, None, error_msg
                    
                    else:
                        # Client error - don't retry
                        error_msg = f"API error {response.status_code}: {response.text[:200]}"
                        logger.error(error_msg)
                        return False, None, error_msg
            
            except httpx.TimeoutException:
                error_msg = f"Request timeout on attempt {attempt}/{self.retry_attempts}"
                logger.warning(error_msg)
                
                if attempt < self.retry_attempts:
                    await asyncio.sleep(self.retry_delay * attempt)
                    continue
                else:
                    return False, None, "Request timeout after retries"
            
            except Exception as e:
                error_msg = f"Network error: {str(e)}"
                logger.error(error_msg)
                
                if attempt < self.retry_attempts:
                    await asyncio.sleep(self.retry_delay * attempt)
                    continue
                else:
                    return False, None, error_msg
        
        return False, None, "Max retries exceeded"
    
    async def sync_updates(
        self,
        session: AsyncSession,
        limit: int = 50
    ) -> Dict[str, int]:
        """
        Sync updates for already exported acts that have new processing.
        
        This handles:
        - New articles processed after initial export
        - New annexes processed after initial export
        - Updates to existing content
        
        Args:
            session: Database session
            limit: Maximum number of acts to sync
            
        Returns:
            Statistics: {"success": X, "error": Y}
        """
        logger.info(f"Syncing updates to Issue Monitoring (limit={limit})")
        
        stats = {"success": 0, "error": 0}
        
        # Find acts that were exported but have new processed content
        query = select(ActLegislativ).options(
            selectinload(ActLegislativ.articole),
            selectinload(ActLegislativ.anexe)
        ).where(
            and_(
                ActLegislativ.export_status == 'completed',
                ActLegislativ.issue_monitoring_id.isnot(None),
                or_(
                    # Has articles processed after export
                    ActLegislativ.articole.any(
                        and_(
                            Articol.ai_status == 'completed',
                            Articol.issue_monitoring_id.is_(None)
                        )
                    ),
                    # Has annexes processed after export
                    ActLegislativ.anexe.any(
                        and_(
                            Anexa.ai_status == 'completed',
                            Anexa.issue_monitoring_id.is_(None)
                        )
                    )
                )
            )
        ).limit(limit)
        
        result = await session.execute(query)
        acts_to_sync = result.scalars().unique().all()
        
        logger.info(f"Found {len(acts_to_sync)} acts with updates to sync")
        
        for act in acts_to_sync:
            try:
                # Build update package with only new content
                update_package = await self._build_update_package(act)
                
                # Send update to Issue Monitoring
                success, error = await self._send_update_to_api(
                    act.issue_monitoring_id,
                    update_package
                )
                
                if success:
                    # Mark new content as exported
                    for articol in act.articole:
                        if articol.ai_status == 'completed' and not articol.issue_monitoring_id:
                            articol.issue_monitoring_id = act.issue_monitoring_id
                    
                    for anexa in act.anexe:
                        if anexa.ai_status == 'completed' and not anexa.issue_monitoring_id:
                            anexa.issue_monitoring_id = act.issue_monitoring_id
                    
                    await session.commit()
                    stats["success"] += 1
                    logger.info(f"✓ Synced updates for act {act.id}")
                    
                else:
                    stats["error"] += 1
                    logger.error(f"✗ Failed to sync act {act.id}: {error}")
            
            except Exception as e:
                logger.error(f"Error syncing act {act.id}: {e}")
                stats["error"] += 1
        
        logger.info(f"Sync completed: {stats}")
        return stats
    
    async def _build_update_package(self, act: ActLegislativ) -> Dict:
        """Build package containing only new/updated content."""
        return {
            "act_id": act.issue_monitoring_id,
            "new_articles": [
                {
                    "id": art.id,
                    "numar": art.numar_articol,
                    "continut": art.continut,
                    "metadata": art.metadate
                }
                for art in act.articole
                if art.ai_status == 'completed' and not art.issue_monitoring_id
            ],
            "new_annexes": [
                {
                    "id": anex.id,
                    "numar": anex.anexa_nr,
                    "continut": anex.continut[:1000],
                    "metadata": anex.metadate
                }
                for anex in act.anexe
                if anex.ai_status == 'completed' and not anex.issue_monitoring_id
            ]
        }
    
    async def _send_update_to_api(
        self,
        im_id: str,
        update_package: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Send update package to Issue Monitoring API."""
        if not self.api_key:
            return False, "API key not configured"
        
        endpoint = f"{self.api_url}/legislation/{im_id}/update"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    endpoint,
                    json=update_package,
                    headers=headers
                )
                
                if response.status_code in [200, 204]:
                    return True, None
                else:
                    return False, f"API error {response.status_code}"
        
        except Exception as e:
            return False, str(e)


# Need to import asyncio for sleep
import asyncio

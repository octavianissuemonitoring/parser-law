"""
Stats API Routes - Statistics and metrics
"""
from typing import Dict, Any
from fastapi import APIRouter
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBSession
from app.models import ActLegislativ, Articol, LinkLegislatie

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/", response_model=Dict[str, Any])
async def get_statistics(db: DBSession):
    """
    Get comprehensive statistics about the system.
    
    Returns:
        - Total counts (acts, articles, links)
        - Acts by type distribution
        - Acts by year distribution
        - Processing status breakdown
        - Recent activity metrics
    """
    
    # Total counts
    total_acts = await db.scalar(select(func.count(ActLegislativ.id)))
    total_articles = await db.scalar(select(func.count(Articol.id)))
    total_links = await db.scalar(select(func.count(LinkLegislatie.id)))
    
    # Links by status
    pending_links = await db.scalar(
        select(func.count(LinkLegislatie.id)).where(
            LinkLegislatie.status == "pending_scraping"
        )
    )
    processing_links = await db.scalar(
        select(func.count(LinkLegislatie.id)).where(
            LinkLegislatie.status == "processing"
        )
    )
    completed_links = await db.scalar(
        select(func.count(LinkLegislatie.id)).where(
            LinkLegislatie.status == "completed"
        )
    )
    failed_links = await db.scalar(
        select(func.count(LinkLegislatie.id)).where(
            LinkLegislatie.status == "failed"
        )
    )
    
    # Acts by type
    acts_by_type_query = select(
        ActLegislativ.tip_act,
        func.count(ActLegislativ.id).label("count")
    ).group_by(ActLegislativ.tip_act).order_by(func.count(ActLegislativ.id).desc())
    
    acts_by_type_result = await db.execute(acts_by_type_query)
    acts_by_type = {row.tip_act: row.count for row in acts_by_type_result}
    
    # Acts by year (last 10 years)
    acts_by_year_query = select(
        ActLegislativ.an_act,
        func.count(ActLegislativ.id).label("count")
    ).where(
        ActLegislativ.an_act.isnot(None)
    ).group_by(ActLegislativ.an_act).order_by(ActLegislativ.an_act.desc()).limit(10)
    
    acts_by_year_result = await db.execute(acts_by_year_query)
    acts_by_year = {str(row.an_act): row.count for row in acts_by_year_result}
    
    # Last import timestamp
    last_import_query = select(ActLegislativ.created_at).order_by(
        ActLegislativ.created_at.desc()
    ).limit(1)
    last_import_result = await db.execute(last_import_query)
    last_import = last_import_result.scalar()
    
    # Recent changes (acts modified in last 30 days)
    recent_changes_query = select(func.count(ActLegislativ.id)).where(
        ActLegislativ.updated_at > func.now() - func.cast("30 days", type_=func.text("interval"))
    )
    recent_changes = await db.scalar(recent_changes_query)
    
    # Average articles per act
    avg_articles_per_act = 0
    if total_acts and total_acts > 0:
        avg_articles_per_act = round(total_articles / total_acts, 1)
    
    return {
        "total_acts": total_acts or 0,
        "total_articles": total_articles or 0,
        "total_links": total_links or 0,
        "avg_articles_per_act": avg_articles_per_act,
        "processing_status": {
            "pending": pending_links or 0,
            "processing": processing_links or 0,
            "completed": completed_links or 0,
            "failed": failed_links or 0
        },
        "acts_by_type": acts_by_type,
        "acts_by_year": acts_by_year,
        "recent_changes_30d": recent_changes or 0,
        "last_import": last_import.isoformat() if last_import else None
    }

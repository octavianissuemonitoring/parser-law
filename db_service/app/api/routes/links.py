"""
Links Management API Routes - Endpoints for managing legislation source links.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import subprocess
import logging

from app.api.deps import get_db
from app.models.link_legislatie import LinkLegislatie, LinkStatus

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/links", tags=["Links Management"])


# Pydantic Models
class LinkCreate(BaseModel):
    """Request to add a new link."""
    url: HttpUrl = Field(..., description="Legislation URL to scrape")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")


class LinkResponse(BaseModel):
    """Link information."""
    id: int
    url: str
    status: str
    acte_count: int = Field(description="Number of acts from this link")
    error_message: Optional[str] = None
    created_at: datetime
    last_scraped_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LinksStats(BaseModel):
    """Statistics about links."""
    total_acts: int  # For UI compatibility
    total_unique_links: int  # For UI compatibility
    pending_links: int
    completed_links: int
    failed_links: int
    top_sources: List[dict] = []  # Top sources by acts count


# Endpoints

@router.post("/", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def add_link(
    link_data: LinkCreate,
    db: AsyncSession = Depends(get_db)
) -> LinkResponse:
    """
    Add a new legislation link to scrape.
    
    This endpoint registers a new URL to be scraped for legislative acts.
    The URL will have status 'pending_scraping' until processed.
    """
    
    # Check if link already exists
    query = select(LinkLegislatie).where(LinkLegislatie.url == str(link_data.url))
    result = await db.execute(query)
    existing_link = result.scalar_one_or_none()
    
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Link already exists with ID {existing_link.id}"
        )
    
    # Create new link
    new_link = LinkLegislatie(
        url=str(link_data.url),
        status=LinkStatus.PENDING
    )
    
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    
    return LinkResponse.from_orm(new_link)


@router.get("/stats", response_model=LinksStats)
async def get_links_stats(db: AsyncSession = Depends(get_db)) -> LinksStats:
    """
    Get statistics about legislation links.
    
    Returns:
    - Total number of acts in database
    - Total unique links
    - Counts by status (pending, completed, failed)
    - Top sources by acts count
    """
    
    # Total acts from acte_legislative table
    from app.models.act_legislativ import ActLegislativ
    acts_count_query = select(func.count(ActLegislativ.id))
    acts_count_result = await db.execute(acts_count_query)
    total_acts = acts_count_result.scalar() or 0
    
    # Total links
    total_query = select(func.count(LinkLegislatie.id))
    total_result = await db.execute(total_query)
    total_unique_links = total_result.scalar() or 0
    
    # Count by status
    pending_query = select(func.count(LinkLegislatie.id)).where(LinkLegislatie.status == LinkStatus.PENDING)
    pending_result = await db.execute(pending_query)
    pending_links = pending_result.scalar() or 0
    
    completed_query = select(func.count(LinkLegislatie.id)).where(LinkLegislatie.status == LinkStatus.COMPLETED)
    completed_result = await db.execute(completed_query)
    completed_links = completed_result.scalar() or 0
    
    failed_query = select(func.count(LinkLegislatie.id)).where(LinkLegislatie.status == LinkStatus.FAILED)
    failed_result = await db.execute(failed_query)
    failed_links = failed_result.scalar() or 0
    
    # Top sources (links with most acts)
    top_sources_query = select(LinkLegislatie).where(LinkLegislatie.acte_count > 0).order_by(LinkLegislatie.acte_count.desc()).limit(10)
    top_sources_result = await db.execute(top_sources_query)
    top_sources_links = top_sources_result.scalars().all()
    
    top_sources = [
        {
            "url": link.url,
            "acts_count": link.acte_count
        }
        for link in top_sources_links
    ]
    
    return LinksStats(
        total_acts=total_acts,
        total_unique_links=total_unique_links,
        pending_links=pending_links,
        completed_links=completed_links,
        failed_links=failed_links,
        top_sources=top_sources
    )


@router.get("/", response_model=dict)
async def get_links(
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get all legislation links with pagination.
    
    Parameters:
    - limit: Maximum number of links to return (default: 50)
    - skip: Number of links to skip (default: 0)
    
    Returns list of links with metadata.
    """
    
    # Count total
    count_query = select(func.count(LinkLegislatie.id))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Get links
    query = select(LinkLegislatie).order_by(LinkLegislatie.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    links = result.scalars().all()
    
    # Build response
    return {
        "total": total,
        "items": [LinkResponse.from_orm(link) for link in links]
    }


@router.post("/process", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def process_link(
    url: HttpUrl,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Trigger scraping and import for a specific legislation URL.
    
    This endpoint starts a background job to:
    1. Update link status to 'processing'
    2. Run scraper on the provided URL
    3. Update link status to 'completed' or 'failed'
    
    The processing happens asynchronously.
    """
    
    # Find or create link
    query = select(LinkLegislatie).where(LinkLegislatie.url == str(url))
    result = await db.execute(query)
    link = result.scalar_one_or_none()
    
    if not link:
        # Create new link
        link = LinkLegislatie(url=str(url), status=LinkStatus.PROCESSING)
        db.add(link)
    else:
        # Update existing link
        link.status = LinkStatus.PROCESSING
        link.updated_at = datetime.utcnow()
    
    await db.commit()
    link_id = link.id
    
    def run_scraper_and_import(url_str: str, link_id: int):
        """Background task to run scraper and import."""
        from sqlalchemy import create_engine, update
        from sqlalchemy.orm import sessionmaker
        from app.config import settings
        
        # Create synchronous engine for background task
        sync_database_url = settings.database_url.replace('postgresql+asyncpg://', 'postgresql://')
        engine = create_engine(sync_database_url)
        SessionLocal = sessionmaker(bind=engine)
        
        def update_link_status_sync(link_id: int, status: str, error: Optional[str] = None):
            """Update link status in database synchronously."""
            with SessionLocal() as session:
                stmt = update(LinkLegislatie).where(LinkLegislatie.id == link_id).values(
                    status=status,
                    updated_at=datetime.utcnow(),
                    last_scraped_at=datetime.utcnow(),
                    error_message=error
                )
                session.execute(stmt)
                session.commit()
        
        try:
            # Run scraper
            logger.info(f"Starting scraper for URL: {url_str}")
            result = subprocess.run(
                ["python", "/app/scraper_legislatie.py", "--url", url_str],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )
            
            if result.returncode != 0:
                error_msg = f"Scraper failed: {result.stderr[:500]}"
                logger.error(error_msg)
                update_link_status_sync(link_id, LinkStatus.FAILED, error_msg)
                return
            
            logger.info(f"Scraper completed successfully for {url_str}")
            logger.info(f"Scraper output: {result.stdout[:1000]}")
            
            # Import CSV files using asyncio in a sync context
            logger.info("Starting import of CSV files...")
            import asyncio
            from app.services import run_import
            
            try:
                # Run async import function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                import_result = loop.run_until_complete(run_import("/app/rezultate"))
                loop.close()
                
                logger.info(f"Import completed: {import_result}")
                
                # Count imported acts from this source
                with SessionLocal() as session:
                    from app.models import ActLegislativ
                    acte_count = session.query(ActLegislativ).filter(
                        ActLegislativ.url_sursa == url_str
                    ).count()
                    
                    stmt = update(LinkLegislatie).where(LinkLegislatie.id == link_id).values(
                        status=LinkStatus.COMPLETED,
                        acte_count=acte_count,
                        updated_at=datetime.utcnow(),
                        last_scraped_at=datetime.utcnow(),
                        error_message=None
                    )
                    session.execute(stmt)
                    session.commit()
                    logger.info(f"Link completed with {acte_count} acts imported")
                    
            except Exception as e:
                error_msg = f"Import failed: {str(e)[:500]}"
                logger.error(error_msg)
                update_link_status_sync(link_id, LinkStatus.FAILED, error_msg)
                return
            
        except subprocess.TimeoutExpired:
            error_msg = f"Scraper timeout (>10 minutes)"
            logger.error(error_msg)
            update_link_status_sync(link_id, LinkStatus.FAILED, error_msg)
        except Exception as e:
            error_msg = f"Error processing: {str(e)[:500]}"
            logger.error(error_msg)
            update_link_status_sync(link_id, LinkStatus.FAILED, error_msg)
    
    # Add to background tasks
    background_tasks.add_task(run_scraper_and_import, str(url), link_id)
    
    return {
        "status": "processing",
        "message": f"Started scraping for {url}. Check link status for updates.",
        "url": str(url),
        "link_id": link_id
    }

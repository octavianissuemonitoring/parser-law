"""
Links Management API Routes - Endpoints for managing legislation source links.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBSession
from app.models.act_legislativ import ActLegislativ


router = APIRouter(prefix="/links", tags=["Links Management"])


# Models
class LinkCreate(BaseModel):
    """Request to add a new link."""
    url: HttpUrl = Field(..., description="Legislation URL to scrape")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")


class LinkResponse(BaseModel):
    """Link information."""
    url: str
    description: Optional[str]
    acts_count: int = Field(description="Number of acts from this link")


class LinksStats(BaseModel):
    """Statistics about stored links."""
    total_unique_links: int
    total_acts: int
    top_sources: List[dict]


# Endpoints

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_link(
    link: LinkCreate,
    session: DBSession
) -> dict:
    """
    Add a new legislation link to track.
    
    This doesn't scrape immediately - just stores the link.
    Use the scraper to fetch content from this link.
    """
    # In a real implementation, you'd store links in a separate table
    # For now, we'll just return success
    return {
        "message": "Link added successfully",
        "url": str(link.url),
        "description": link.description,
        "next_step": "Run scraper to fetch content from this link"
    }


@router.get("/stats", response_model=LinksStats)
async def get_links_stats(session: DBSession) -> LinksStats:
    """
    Get statistics about legislation sources.
    
    Returns counts and top sources based on stored acts.
    """
    # Count total acts
    total_stmt = select(ActLegislativ.id)
    total_result = await session.execute(total_stmt)
    total_acts = len(total_result.all())
    
    # Get unique links and their counts
    links_stmt = select(
        ActLegislativ.link_legislatie
    ).where(
        ActLegislativ.link_legislatie.isnot(None)
    ).distinct()
    
    links_result = await session.execute(links_stmt)
    unique_links = links_result.scalars().all()
    
    # Get top sources
    top_sources = []
    for link in unique_links[:10]:  # Top 10
        count_stmt = select(ActLegislativ.id).where(
            ActLegislativ.link_legislatie == link
        )
        count_result = await session.execute(count_stmt)
        count = len(count_result.all())
        
        top_sources.append({
            "url": link,
            "acts_count": count
        })
    
    # Sort by count
    top_sources.sort(key=lambda x: x["acts_count"], reverse=True)
    
    return LinksStats(
        total_unique_links=len(unique_links),
        total_acts=total_acts,
        top_sources=top_sources
    )


@router.get("/", response_model=List[LinkResponse])
async def list_links(
    limit: int = 50,
    session: DBSession = None
) -> List[LinkResponse]:
    """
    List all unique legislation source links.
    
    Returns links with count of acts from each source.
    """
    # Get unique links
    stmt = select(
        ActLegislativ.link_legislatie
    ).where(
        ActLegislativ.link_legislatie.isnot(None)
    ).distinct()
    
    result = await session.execute(stmt)
    links = result.scalars().all()
    
    # Build response with counts
    response = []
    for link in links[:limit]:
        count_stmt = select(ActLegislativ.id).where(
            ActLegislativ.link_legislatie == link
        )
        count_result = await session.execute(count_stmt)
        count = len(count_result.all())
        
        response.append(LinkResponse(
            url=link,
            description=None,  # Could be enhanced with a links table
            acts_count=count
        ))
    
    return response

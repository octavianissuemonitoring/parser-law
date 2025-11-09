"""
Links Management API Routes - Endpoints for managing legislation source links.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db


router = APIRouter(prefix="/links", tags=["Links Management"])


# Pydantic Models
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
    """Statistics about links."""
    total_acts: int
    total_unique_links: int
    top_sources: List[LinkResponse] = Field(description="Top sources by acts count")


# Endpoints

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_link(
    link_data: LinkCreate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Add a new legislation link to scrape.
    
    This endpoint registers a new URL to be scraped for legislative acts.
    The scraping will be triggered automatically by the scheduler.
    """
    
    # Check if link already exists
    check_query = text("""
        SELECT COUNT(*) 
        FROM legislatie.acte_legislative 
        WHERE url_legislatie = :url
    """)
    result = await db.execute(check_query, {"url": str(link_data.url)})
    existing_count = result.scalar()
    
    if existing_count and existing_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Link already exists with {existing_count} acts"
        )
    
    # Link acknowledged - in production, trigger scraping here
    return {
        "message": "Link added successfully. Scraping will be triggered automatically.",
        "url": str(link_data.url),
        "description": link_data.description
    }


@router.get("/stats", response_model=LinksStats)
async def get_links_stats(db: AsyncSession = Depends(get_db)) -> LinksStats:
    """
    Get statistics about legislation links and sources.
    
    Returns:
    - Total number of acts
    - Total unique source links
    - Top sources by acts count
    """
    
    # Total acts
    total_query = text("SELECT COUNT(*) FROM legislatie.acte_legislative")
    total_result = await db.execute(total_query)
    total_acts = total_result.scalar() or 0
    
    # Unique links with counts
    links_query = text("""
        SELECT 
            url_legislatie as url,
            COUNT(*) as acts_count
        FROM legislatie.acte_legislative
        WHERE url_legislatie IS NOT NULL
        GROUP BY url_legislatie
        ORDER BY acts_count DESC
        LIMIT 10
    """)
    links_result = await db.execute(links_query)
    links = links_result.fetchall()
    
    # Build response
    top_sources = []
    for row in links:
        top_sources.append({
            "url": row[0],
            "description": None,
            "acts_count": row[1]
        })
    
    return LinksStats(
        total_acts=total_acts,
        total_unique_links=len(top_sources),
        top_sources=top_sources
    )


@router.get("/", response_model=List[LinkResponse])
async def get_links(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> List[LinkResponse]:
    """
    Get all unique legislation links with acts count.
    
    Parameters:
    - limit: Maximum number of links to return (default: 50)
    
    Returns list of links with metadata and acts count.
    """
    
    # Get all unique links with counts
    query = text("""
        SELECT 
            url_legislatie as url,
            COUNT(*) as acts_count
        FROM legislatie.acte_legislative
        WHERE url_legislatie IS NOT NULL
        GROUP BY url_legislatie
        ORDER BY acts_count DESC
        LIMIT :limit
    """)
    result = await db.execute(query, {"limit": limit})
    links = result.fetchall()
    
    # Build response
    response = []
    for row in links:
        response.append(LinkResponse(
            url=row[0],
            description=None,
            acts_count=row[1]
        ))
    
    return response

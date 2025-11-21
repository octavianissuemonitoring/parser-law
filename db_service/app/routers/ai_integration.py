"""
API Routes for AI Service Integration.

Endpoints for AI service to:
- Fetch articles for processing (by status)
- Update AI processing status
- Batch operations
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.articol import Articol
from app.models.ai_status import AIStatus
from app.schemas.articol_schema import (
    ArticolResponse,
    ArticolAIStatusUpdate,
    ArticolAIBatchResponse
)

router = APIRouter(prefix="/ai", tags=["AI Service"])


@router.get("/articles/pending", response_model=List[ArticolResponse])
async def get_pending_articles(
    limit: int = Query(100, ge=1, le=1000, description="Max articles to return"),
    act_id: Optional[int] = Query(None, description="Filter by act ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get articles pending AI processing (ai_status=0).
    
    Used by AI service to fetch articles that need processing.
    """
    query = select(Articol).where(Articol.ai_status == AIStatus.NOT_PROCESSED)
    
    if act_id:
        query = query.where(Articol.act_id == act_id)
    
    query = query.limit(limit).order_by(Articol.id)
    
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return articles


@router.get("/articles/by-status/{status}", response_model=List[ArticolResponse])
async def get_articles_by_status(
    status: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get articles by AI processing status.
    
    Status codes:
    - 0: Not processed
    - 1: Processing
    - 2: Processed
    - 9: Error
    """
    if status not in [0, 1, 2, 9]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 0, 1, 2, or 9")
    
    query = (
        select(Articol)
        .where(Articol.ai_status == status)
        .limit(limit)
        .offset(offset)
        .order_by(Articol.id)
    )
    
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return articles


@router.post("/articles/mark-processing", response_model=ArticolAIBatchResponse)
async def mark_articles_processing(
    article_ids: List[int],
    db: AsyncSession = Depends(get_db)
):
    """
    Mark articles as being processed (ai_status=1).
    
    AI service should call this when starting to process a batch.
    """
    try:
        stmt = (
            update(Articol)
            .where(Articol.id.in_(article_ids))
            .values(ai_status=AIStatus.PROCESSING)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return ArticolAIBatchResponse(
            success=True,
            updated_count=result.rowcount,
            message=f"Marked {result.rowcount} articles as processing"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update: {str(e)}")


@router.post("/articles/update-status", response_model=ArticolAIBatchResponse)
async def update_ai_status(
    update_data: ArticolAIStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update AI processing status for multiple articles.
    
    This is the main endpoint for AI service to report results.
    
    Examples:
    - Mark as processed: {"article_ids": [1,2,3], "ai_status": 2, "metadate": "summary..."}
    - Mark as error: {"article_ids": [4], "ai_status": 9, "ai_error_message": "Timeout"}
    """
    # Validate that message is provided for important statuses
    if update_data.ai_status == AIStatus.ERROR and not update_data.ai_status_message:
        raise HTTPException(
            status_code=400,
            detail="ai_status_message is recommended when ai_status=9 (error)"
        )
    
    try:
        values = {"ai_status": update_data.ai_status}
        
        # Add timestamp if completing
        if update_data.ai_status in [AIStatus.PROCESSED, AIStatus.ERROR]:
            values["ai_processed_at"] = datetime.utcnow()
        
        # Add metadata if provided
        if update_data.metadate:
            values["metadate"] = update_data.metadate
        
        # Add status message if provided
        if update_data.ai_status_message:
            values["ai_status_message"] = update_data.ai_status_message
        
        stmt = (
            update(Articol)
            .where(Articol.id.in_(update_data.article_ids))
            .values(**values)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        status_name = AIStatus.to_string(update_data.ai_status)
        
        return ArticolAIBatchResponse(
            success=True,
            updated_count=result.rowcount,
            message=f"Updated {result.rowcount} articles to status '{status_name}'"
        )
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


@router.post("/articles/{article_id}/status", response_model=ArticolResponse)
async def update_single_article_status(
    article_id: int,
    ai_status: int = Query(..., ge=0, le=9),
    ai_status_message: Optional[str] = None,
    metadate: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Update AI status for a single article.
    
    Simpler endpoint for single article updates.
    """
    # Fetch article
    result = await db.execute(select(Articol).where(Articol.id == article_id))
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
    
    # Update fields
    article.ai_status = ai_status
    
    if ai_status in [AIStatus.PROCESSED, AIStatus.ERROR]:
        article.ai_processed_at = datetime.utcnow()
    
    if metadate:
        article.metadate = metadate
    
    if ai_status_message:
        article.ai_status_message = ai_status_message
    
    try:
        await db.commit()
        await db.refresh(article)
        return article
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update: {str(e)}")


@router.get("/stats", response_model=dict)
async def get_ai_processing_stats(db: AsyncSession = Depends(get_db)):
    """
    Get statistics about AI processing status.
    
    Returns counts for each status.
    """
    from sqlalchemy import func
    
    query = select(
        Articol.ai_status,
        func.count(Articol.id).label("count")
    ).group_by(Articol.ai_status)
    
    result = await db.execute(query)
    rows = result.all()
    
    stats = {
        "not_processed": 0,
        "processing": 0,
        "processed": 0,
        "error": 0,
        "total": 0
    }
    
    for status, count in rows:
        stats["total"] += count
        status_key = AIStatus.to_string(status)
        if status_key != "unknown":
            stats[status_key] = count
    
    return stats

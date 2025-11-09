"""
AI Processing API Routes - Endpoints for triggering and monitoring AI processing.

These endpoints are protected with API key authentication.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field

from app.api.deps import DBSession, AuthInfo
from app.services.ai_service import AIService
from app.models.articol import Articol
from sqlalchemy import select, func, and_


router = APIRouter(prefix="/ai", tags=["AI Processing"])


# Request/Response Models
class ProcessRequest(BaseModel):
    """Request to trigger AI processing."""
    limit: int = Field(10, ge=1, le=100, description="Maximum number of items to process")
    batch_delay: float = Field(1.0, ge=0.1, le=10.0, description="Delay between batches (seconds)")


class ProcessResponse(BaseModel):
    """Response after triggering AI processing."""
    message: str
    job_id: Optional[str] = None
    processing_in_background: bool


class ProcessStatsResponse(BaseModel):
    """Statistics from AI processing."""
    success: int
    error: int
    skipped: int
    total: int


class AIStatusResponse(BaseModel):
    """Current status of AI processing."""
    pending_count: int
    processing_count: int
    completed_count: int
    error_count: int
    total_count: int


class ArticleStatusResponse(BaseModel):
    """Status of a specific article."""
    id: int
    numar_articol: str
    ai_status: str
    ai_processed_at: Optional[str]
    ai_error: Optional[str]
    has_metadata: bool
    issues_count: int


# Endpoints

@router.post("/process", response_model=ProcessResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_ai_processing(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    session: DBSession,
    auth: AuthInfo
) -> ProcessResponse:
    """
    Trigger AI processing for pending articles.
    
    **Authentication Required:** API Key
    
    This endpoint starts AI processing in the background:
    - Extracts issues from article content
    - Generates metadata summaries
    - Updates database with results
    
    Processing happens asynchronously - use /ai/status to monitor progress.
    """
    # Queue background processing
    ai_service = AIService()
    
    # We'll run this in background
    background_tasks.add_task(
        ai_service.process_pending_articole,
        limit=request.limit,
        batch_delay=request.batch_delay
    )
    
    return ProcessResponse(
        message=f"AI processing started for up to {request.limit} articles",
        job_id=None,  # Could implement job tracking later
        processing_in_background=True
    )


@router.get("/process/sync", response_model=ProcessStatsResponse)
async def trigger_ai_processing_sync(
    limit: int = 10,
    batch_delay: float = 1.0,
    session: DBSession = None,
    auth: AuthInfo = None
) -> ProcessStatsResponse:
    """
    Trigger AI processing synchronously (waits for completion).
    
    **Authentication Required:** API Key
    
    ⚠️ **Warning:** This endpoint blocks until processing completes.
    Use /ai/process for async processing instead.
    
    Useful for testing or processing small batches.
    """
    ai_service = AIService()
    stats = await ai_service.process_pending_articole(
        limit=limit,
        batch_delay=batch_delay
    )
    
    return ProcessStatsResponse(
        success=stats["success"],
        error=stats["error"],
        skipped=stats["skipped"],
        total=stats["success"] + stats["error"] + stats["skipped"]
    )


@router.get("/status", response_model=AIStatusResponse)
async def get_ai_status(
    session: DBSession,
    auth: AuthInfo
) -> AIStatusResponse:
    """
    Get current AI processing status.
    
    **Authentication Required:** API Key
    
    Returns counts of articles in each processing state:
    - pending: Not yet processed
    - processing: Currently being processed
    - completed: Successfully processed
    - error: Failed processing
    """
    # Count articles by status
    stmt = select(
        Articol.ai_status,
        func.count(Articol.id).label("count")
    ).group_by(Articol.ai_status)
    
    result = await session.execute(stmt)
    counts = {row.ai_status: row.count for row in result}
    
    total = await session.scalar(select(func.count(Articol.id)))
    
    return AIStatusResponse(
        pending_count=counts.get("pending", 0),
        processing_count=counts.get("processing", 0),
        completed_count=counts.get("completed", 0),
        error_count=counts.get("error", 0),
        total_count=total or 0
    )


@router.get("/pending", response_model=list[ArticleStatusResponse])
async def get_pending_articles(
    limit: int = 50,
    session: DBSession = None,
    auth: AuthInfo = None
) -> list[ArticleStatusResponse]:
    """
    List articles pending AI processing.
    
    **Authentication Required:** API Key
    
    Returns articles with ai_status='pending', ordered by creation date.
    """
    stmt = select(Articol).where(
        Articol.ai_status == "pending"
    ).order_by(Articol.id.desc()).limit(limit)
    
    result = await session.execute(stmt)
    articles = result.scalars().all()
    
    return [
        ArticleStatusResponse(
            id=art.id,
            numar_articol=art.numar_articol,
            ai_status=art.ai_status,
            ai_processed_at=art.ai_processed_at.isoformat() if art.ai_processed_at else None,
            ai_error=art.ai_error,
            has_metadata=bool(art.metadate),
            issues_count=len(art.issues) if hasattr(art, 'issues') else 0
        )
        for art in articles
    ]


@router.get("/errors", response_model=list[ArticleStatusResponse])
async def get_failed_articles(
    limit: int = 50,
    session: DBSession = None,
    auth: AuthInfo = None
) -> list[ArticleStatusResponse]:
    """
    List articles that failed AI processing.
    
    **Authentication Required:** API Key
    
    Returns articles with ai_status='error', includes error messages.
    """
    stmt = select(Articol).where(
        Articol.ai_status == "error"
    ).order_by(Articol.ai_processed_at.desc()).limit(limit)
    
    result = await session.execute(stmt)
    articles = result.scalars().all()
    
    return [
        ArticleStatusResponse(
            id=art.id,
            numar_articol=art.numar_articol,
            ai_status=art.ai_status,
            ai_processed_at=art.ai_processed_at.isoformat() if art.ai_processed_at else None,
            ai_error=art.ai_error,
            has_metadata=bool(art.metadate),
            issues_count=len(art.issues) if hasattr(art, 'issues') else 0
        )
        for art in articles
    ]


@router.post("/retry/{article_id}", response_model=ArticleStatusResponse)
async def retry_article_processing(
    article_id: int,
    session: DBSession,
    auth: AuthInfo
) -> ArticleStatusResponse:
    """
    Retry AI processing for a specific article.
    
    **Authentication Required:** API Key
    
    Useful for retrying articles that failed processing.
    Resets ai_status to 'pending' and clears error message.
    """
    # Get article
    stmt = select(Articol).where(Articol.id == article_id)
    result = await session.execute(stmt)
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found"
        )
    
    # Process immediately
    ai_service = AIService()
    success, error = await ai_service.process_articol(article_id, session)
    
    # Refresh article to get updated data
    await session.refresh(article)
    
    return ArticleStatusResponse(
        id=article.id,
        numar_articol=article.numar_articol,
        ai_status=article.ai_status,
        ai_processed_at=article.ai_processed_at.isoformat() if article.ai_processed_at else None,
        ai_error=article.ai_error,
        has_metadata=bool(article.metadate),
        issues_count=len(article.issues) if hasattr(article, 'issues') else 0
    )


@router.post("/reset/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def reset_article_status(
    article_id: int,
    session: DBSession,
    auth: AuthInfo
):
    """
    Reset article AI status to 'pending'.
    
    **Authentication Required:** API Key
    
    Clears AI processing state without reprocessing.
    Use this to queue article for reprocessing later.
    """
    stmt = select(Articol).where(Articol.id == article_id)
    result = await session.execute(stmt)
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found"
        )
    
    article.ai_status = "pending"
    article.ai_error = None
    article.ai_processed_at = None
    
    await session.commit()

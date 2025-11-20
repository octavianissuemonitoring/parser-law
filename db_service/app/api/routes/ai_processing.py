"""
AI Processing API Routes - All AI-related endpoints.

Includes:
1. Document retrieval for AI processing (acts with full structure)
2. AI processing triggers and monitoring
3. Status management (mark as processing/processed/error)

These endpoints are used by external AI services and internal automation.
"""
from typing import Optional, List, Dict
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, AuthInfo
from app.services.ai_service import AIService
from app.models import Articol, ActLegislativ, ActDomeniu, Domeniu
from app.schemas import DomeniuMinimal


router = APIRouter(prefix="/ai", tags=["AI Processing"])


# ============================================================================
# Request/Response Models
# ============================================================================

# --- Processing Control Models ---
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


# --- Document Structure Models for AI ---
class ArticolForAI(BaseModel):
    """Article structure for AI processing."""
    id: int
    articol_nr: Optional[str]
    articol_label: Optional[str]
    
    # Hierarchy
    titlu_nr: Optional[int]
    titlu_denumire: Optional[str]
    capitol_nr: Optional[int]
    capitol_denumire: Optional[str]
    sectiune_nr: Optional[int]
    sectiune_denumire: Optional[str]
    
    # Content
    text_articol: str
    ordine: Optional[int]
    
    # AI Status
    ai_status: Optional[str]
    ai_processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ActForAI(BaseModel):
    """Complete act structure for AI processing."""
    
    # Act metadata
    id: int
    tip_act: str
    nr_act: Optional[str]
    data_act: Optional[str]
    an_act: Optional[int]
    titlu_act: str
    emitent_act: Optional[str]
    url_legislatie: Optional[str]
    
    # AI Status
    ai_status: Optional[str]
    ai_processed_at: Optional[datetime]
    
    # Domains assigned to this act
    domenii: List[DomeniuMinimal]
    
    # Complete article structure
    articole: List[ArticolForAI]
    
    # Statistics
    total_articole: int
    pending_articole: int


class ActListItemForAI(BaseModel):
    """Minimal act info for list view."""
    id: int
    tip_act: str
    nr_act: Optional[str]
    an_act: Optional[int]
    titlu_act: str
    ai_status: Optional[str]
    total_articole: int
    pending_articole: int
    domenii: List[DomeniuMinimal]


# ============================================================================
# ENDPOINTS - Document Retrieval for AI
# ============================================================================

@router.get("/acte/pending", response_model=List[ActListItemForAI])
async def get_acts_for_processing(
    db: DBSession,
    ai_status: str = Query(default="pending", description="Filter: pending, processing, processed, error"),
    has_domenii: Optional[bool] = Query(None, description="Filter acts with domains assigned"),
    limit: int = Query(default=10, ge=1, le=100),
) -> List[ActListItemForAI]:
    """
    **[AI Service]** Get list of acts needing processing.
    
    Returns acts filtered by `ai_status` with assigned domains and article counts.
    Use this to discover which acts need AI analysis.
    
    **Flow:**
    1. Call this endpoint to get acts with `ai_status=pending`
    2. For each act, call `GET /ai/acte/{id}` to get full structure
    3. Analyze articles and post issues via `POST /issues/link`
    """
    # Build query
    query = select(ActLegislativ).where(ActLegislativ.ai_status == ai_status)
    
    # Filter by domain presence
    if has_domenii is True:
        query = query.join(ActDomeniu, ActLegislativ.id == ActDomeniu.act_id)
    elif has_domenii is False:
        query = query.outerjoin(ActDomeniu, ActLegislativ.id == ActDomeniu.act_id).where(ActDomeniu.id == None)
    
    query = query.order_by(ActLegislativ.created_at.desc()).limit(limit)
    result = await db.execute(query)
    acte = result.scalars().all()
    
    # Build response with statistics
    response = []
    for act in acte:
        # Get domains
        domenii_query = (
            select(Domeniu)
            .join(ActDomeniu, Domeniu.id == ActDomeniu.domeniu_id)
            .where(ActDomeniu.act_id == act.id)
            .where(Domeniu.activ == True)
        )
        domenii_result = await db.execute(domenii_query)
        domenii = domenii_result.scalars().all()
        
        # Get article counts
        total_result = await db.execute(select(func.count()).where(Articol.act_id == act.id))
        total_articole = total_result.scalar() or 0
        
        pending_result = await db.execute(
            select(func.count()).where(and_(Articol.act_id == act.id, Articol.ai_status == 'pending'))
        )
        pending_articole = pending_result.scalar() or 0
        
        response.append(ActListItemForAI(
            id=act.id,
            tip_act=act.tip_act,
            nr_act=act.nr_act,
            an_act=act.an_act,
            titlu_act=act.titlu_act,
            ai_status=act.ai_status,
            total_articole=total_articole,
            pending_articole=pending_articole,
            domenii=[DomeniuMinimal(id=d.id, cod=d.cod, denumire=d.denumire, culoare=d.culoare) for d in domenii]
        ))
    
    return response


@router.get("/acte/{act_id}", response_model=ActForAI)
async def get_act_full_structure(
    act_id: int,
    db: DBSession,
    include_processed: bool = Query(default=False, description="Include already processed articles"),
) -> ActForAI:
    """
    **[AI Service]** Get complete act with ALL articles for processing.
    
    **This is the main endpoint for retrieving document structure.**
    
    Returns:
    - Act metadata (title, type, year, URL)
    - All assigned domains
    - Complete article list with:
      - Full text (`text_articol`)
      - Hierarchy info (`titlu_nr`, `capitol_nr`, `sectiune_nr`)
      - AI processing status
    
    **Usage:**
    ```python
    act = GET /ai/acte/123
    
    for article in act.articole:
        if article.ai_status == "pending":
            # Analyze
            issues = ai_analyze(article.text_articol)
            
            # Link issues
            for domain in act.domenii:
                POST /issues/link {...}
    ```
    """
    # Get act with relationships
    query = (
        select(ActLegislativ)
        .where(ActLegislativ.id == act_id)
        .options(selectinload(ActLegislativ.articole))
    )
    result = await db.execute(query)
    act = result.scalar_one_or_none()
    
    if not act:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act {act_id} not found"
        )
    
    # Get domains
    domenii_query = (
        select(Domeniu)
        .join(ActDomeniu, Domeniu.id == ActDomeniu.domeniu_id)
        .where(ActDomeniu.act_id == act_id)
        .where(Domeniu.activ == True)
    )
    domenii_result = await db.execute(domenii_query)
    domenii = domenii_result.scalars().all()
    
    # Get articles
    articole_query = select(Articol).where(Articol.act_id == act_id).order_by(Articol.ordine)
    if not include_processed:
        articole_query = articole_query.where(Articol.ai_status == 'pending')
    
    articole_result = await db.execute(articole_query)
    articole = articole_result.scalars().all()
    
    # Statistics
    total_result = await db.execute(select(func.count()).where(Articol.act_id == act_id))
    total_articole = total_result.scalar() or 0
    
    pending_result = await db.execute(
        select(func.count()).where(and_(Articol.act_id == act_id, Articol.ai_status == 'pending'))
    )
    pending_articole = pending_result.scalar() or 0
    
    return ActForAI(
        id=act.id,
        tip_act=act.tip_act,
        nr_act=act.nr_act,
        data_act=act.data_act.isoformat() if act.data_act else None,
        an_act=act.an_act,
        titlu_act=act.titlu_act,
        emitent_act=act.emitent_act,
        url_legislatie=act.url_legislatie,
        ai_status=act.ai_status,
        ai_processed_at=act.ai_processed_at,
        domenii=[DomeniuMinimal(id=d.id, cod=d.cod, denumire=d.denumire, culoare=d.culoare) for d in domenii],
        articole=[
            ArticolForAI(
                id=a.id,
                articol_nr=a.articol_nr,
                articol_label=a.articol_label,
                titlu_nr=a.titlu_nr,
                titlu_denumire=a.titlu_denumire,
                capitol_nr=a.capitol_nr,
                capitol_denumire=a.capitol_denumire,
                sectiune_nr=a.sectiune_nr,
                sectiune_denumire=a.sectiune_denumire,
                text_articol=a.text_articol,
                ordine=a.ordine,
                ai_status=a.ai_status,
                ai_processed_at=a.ai_processed_at,
            ) for a in articole
        ],
        total_articole=total_articole,
        pending_articole=pending_articole,
    )


@router.post("/articole/{articol_id}/mark-processing", status_code=status.HTTP_204_NO_CONTENT)
async def mark_article_processing(articol_id: int, db: DBSession):
    """
    **[AI Service]** Mark article as currently being processed.
    
    Sets `ai_status='processing'` to prevent duplicate processing.
    Call this before starting AI analysis of an article.
    """
    result = await db.execute(select(Articol).where(Articol.id == articol_id))
    articol = result.scalar_one_or_none()
    
    if not articol:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Articol {articol_id} not found")
    
    articol.ai_status = 'processing'
    await db.commit()


@router.post("/articole/{articol_id}/mark-processed", status_code=status.HTTP_204_NO_CONTENT)
async def mark_article_processed(articol_id: int, db: DBSession):
    """
    **[AI Service]** Mark article as successfully processed.
    
    Sets `ai_status='processed'` and records timestamp.
    Call this after successfully analyzing article and posting issues.
    """
    result = await db.execute(select(Articol).where(Articol.id == articol_id))
    articol = result.scalar_one_or_none()
    
    if not articol:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Articol {articol_id} not found")
    
    articol.ai_status = 'processed'
    articol.ai_processed_at = datetime.utcnow()
    await db.commit()


@router.post("/articole/{articol_id}/mark-error")
async def mark_article_error(
    articol_id: int,
    db: DBSession,
    error_message: str = Query(..., description="Error message"),
):
    """
    **[AI Service]** Mark article as failed during processing.
    
    Sets `ai_status='error'` and stores error message.
    Call this if AI analysis fails for an article.
    """
    result = await db.execute(select(Articol).where(Articol.id == articol_id))
    articol = result.scalar_one_or_none()
    
    if not articol:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Articol {articol_id} not found")
    
    articol.ai_status = 'error'
    articol.ai_error = error_message
    await db.commit()
    
    return {"message": "Article marked as error", "error": error_message}


# ============================================================================
# ENDPOINTS - Processing Control & Monitoring
# ============================================================================
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
            numar_articol=art.articol_nr,
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
            numar_articol=art.articol_nr,
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
        numar_articol=article.articol_nr,
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

"""
Export API Routes - Endpoints for exporting to Issue Monitoring platform.

These endpoints are protected with API key authentication.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field

from app.api.deps import DBSession, AuthInfo
from app.services.export_service import ExportService
from app.models.act_legislativ import ActLegislativ
from sqlalchemy import select, func, and_


router = APIRouter(prefix="/export", tags=["Export"])


# Request/Response Models
class ExportRequest(BaseModel):
    """Request to trigger export."""
    act_id: Optional[int] = Field(None, description="Specific act ID to export (None = export pending)")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of acts to export")


class ExportResponse(BaseModel):
    """Response after triggering export."""
    message: str
    job_id: Optional[str] = None
    exporting_in_background: bool


class ExportStatsResponse(BaseModel):
    """Statistics from export operation."""
    success: int
    error: int
    skipped: int
    total: int


class ExportStatusResponse(BaseModel):
    """Current export status."""
    pending_count: int
    completed_count: int
    error_count: int
    total_acts_with_ai: int


class ActExportStatusResponse(BaseModel):
    """Export status of a specific act."""
    id: int
    nr_act: str
    an_act: int
    titlu: str
    export_status: str
    export_at: Optional[str]
    export_error: Optional[str]
    issue_monitoring_id: Optional[str]
    ai_status: str
    articles_count: int
    issues_count: int


# Endpoints

@router.post("/to-im", response_model=ExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def export_to_issue_monitoring(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    session: DBSession,
    auth: AuthInfo
) -> ExportResponse:
    """
    Export processed legislation to Issue Monitoring platform.
    
    **Authentication Required:** API Key
    
    Exports acts with completed AI processing:
    - Builds JSON packages with acts, articles, annexes, and issues
    - Sends to Issue Monitoring API
    - Updates export_status and issue_monitoring_id
    
    Export happens asynchronously - use /export/status to monitor.
    """
    export_service = ExportService()
    
    # Queue background export
    background_tasks.add_task(
        export_service.export_to_issue_monitoring,
        session=session,
        act_id=request.act_id,
        limit=request.limit
    )
    
    act_msg = f"act {request.act_id}" if request.act_id else f"up to {request.limit} acts"
    
    return ExportResponse(
        message=f"Export started for {act_msg}",
        job_id=None,
        exporting_in_background=True
    )


@router.post("/to-im/sync", response_model=ExportStatsResponse)
async def export_to_issue_monitoring_sync(
    act_id: Optional[int] = None,
    limit: int = 10,
    session: DBSession = None,
    auth: AuthInfo = None
) -> ExportStatsResponse:
    """
    Export to Issue Monitoring synchronously (waits for completion).
    
    **Authentication Required:** API Key
    
    ⚠️ **Warning:** This endpoint blocks until export completes.
    Use /export/to-im for async export instead.
    """
    export_service = ExportService()
    stats = await export_service.export_to_issue_monitoring(
        session=session,
        act_id=act_id,
        limit=limit
    )
    
    return ExportStatsResponse(
        success=stats["success"],
        error=stats["error"],
        skipped=stats["skipped"],
        total=stats["success"] + stats["error"] + stats["skipped"]
    )


@router.post("/sync-updates", response_model=ExportStatsResponse)
async def sync_updates_to_issue_monitoring(
    limit: int = 50,
    background_tasks: BackgroundTasks = None,
    session: DBSession = None,
    auth: AuthInfo = None
) -> ExportStatsResponse:
    """
    Sync updates for already exported acts.
    
    **Authentication Required:** API Key
    
    Finds acts that were exported but have new processed articles/annexes,
    and sends incremental updates to Issue Monitoring.
    """
    export_service = ExportService()
    stats = await export_service.sync_updates(
        session=session,
        limit=limit
    )
    
    return ExportStatsResponse(
        success=stats["success"],
        error=stats["error"],
        skipped=0,
        total=stats["success"] + stats["error"]
    )


@router.get("/status", response_model=ExportStatusResponse)
async def get_export_status(
    session: DBSession,
    auth: AuthInfo
) -> ExportStatusResponse:
    """
    Get current export status.
    
    **Authentication Required:** API Key
    
    Returns counts of acts in each export state.
    Only counts acts with ai_status='completed'.
    """
    # Count acts by export status (only AI-completed acts)
    stmt = select(
        ActLegislativ.export_status,
        func.count(ActLegislativ.id).label("count")
    ).where(
        ActLegislativ.ai_status == "completed"
    ).group_by(ActLegislativ.export_status)
    
    result = await session.execute(stmt)
    counts = {row.export_status: row.count for row in result}
    
    # Total AI-completed acts
    total_stmt = select(func.count(ActLegislativ.id)).where(
        ActLegislativ.ai_status == "completed"
    )
    total = await session.scalar(total_stmt)
    
    return ExportStatusResponse(
        pending_count=counts.get("pending", 0),
        completed_count=counts.get("completed", 0),
        error_count=counts.get("error", 0),
        total_acts_with_ai=total or 0
    )


@router.get("/pending", response_model=list[ActExportStatusResponse])
async def get_pending_exports(
    limit: int = 50,
    session: DBSession = None,
    auth: AuthInfo = None
) -> list[ActExportStatusResponse]:
    """
    List acts pending export.
    
    **Authentication Required:** API Key
    
    Returns acts with:
    - ai_status = 'completed'
    - export_status IN ('pending', 'error')
    """
    stmt = select(ActLegislativ).where(
        and_(
            ActLegislativ.ai_status == "completed",
            ActLegislativ.export_status.in_(["pending", "error"])
        )
    ).order_by(ActLegislativ.id.desc()).limit(limit)
    
    result = await session.execute(stmt)
    acts = result.scalars().all()
    
    return [
        ActExportStatusResponse(
            id=act.id,
            nr_act=act.nr_act,
            an_act=act.an_act,
            titlu=act.titlu_act,
            export_status=act.export_status,
            export_at=act.export_at.isoformat() if act.export_at else None,
            export_error=act.export_error,
            issue_monitoring_id=act.issue_monitoring_id,
            ai_status=act.ai_status,
            articles_count=len(act.articole) if hasattr(act, 'articole') else 0,
            issues_count=len(act.issues) if hasattr(act, 'issues') else 0
        )
        for act in acts
    ]


@router.get("/completed", response_model=list[ActExportStatusResponse])
async def get_completed_exports(
    limit: int = 50,
    session: DBSession = None,
    auth: AuthInfo = None
) -> list[ActExportStatusResponse]:
    """
    List successfully exported acts.
    
    **Authentication Required:** API Key
    
    Returns acts with export_status='completed',
    includes issue_monitoring_id for reference.
    """
    stmt = select(ActLegislativ).where(
        ActLegislativ.export_status == "completed"
    ).order_by(ActLegislativ.export_at.desc()).limit(limit)
    
    result = await session.execute(stmt)
    acts = result.scalars().all()
    
    return [
        ActExportStatusResponse(
            id=act.id,
            nr_act=act.nr_act,
            an_act=act.an_act,
            titlu=act.titlu_act,
            export_status=act.export_status,
            export_at=act.export_at.isoformat() if act.export_at else None,
            export_error=act.export_error,
            issue_monitoring_id=act.issue_monitoring_id,
            ai_status=act.ai_status,
            articles_count=len(act.articole) if hasattr(act, 'articole') else 0,
            issues_count=len(act.issues) if hasattr(act, 'issues') else 0
        )
        for act in acts
    ]


@router.get("/errors", response_model=list[ActExportStatusResponse])
async def get_failed_exports(
    limit: int = 50,
    session: DBSession = None,
    auth: AuthInfo = None
) -> list[ActExportStatusResponse]:
    """
    List acts that failed export.
    
    **Authentication Required:** API Key
    
    Returns acts with export_status='error',
    includes error messages for debugging.
    """
    stmt = select(ActLegislativ).where(
        ActLegislativ.export_status == "error"
    ).order_by(ActLegislativ.id.desc()).limit(limit)
    
    result = await session.execute(stmt)
    acts = result.scalars().all()
    
    return [
        ActExportStatusResponse(
            id=act.id,
            nr_act=act.nr_act,
            an_act=act.an_act,
            titlu=act.titlu_act,
            export_status=act.export_status,
            export_at=act.export_at.isoformat() if act.export_at else None,
            export_error=act.export_error,
            issue_monitoring_id=act.issue_monitoring_id,
            ai_status=act.ai_status,
            articles_count=len(act.articole) if hasattr(act, 'articole') else 0,
            issues_count=len(act.issues) if hasattr(act, 'issues') else 0
        )
        for act in acts
    ]


@router.post("/retry/{act_id}", response_model=ActExportStatusResponse)
async def retry_act_export(
    act_id: int,
    session: DBSession,
    auth: AuthInfo
) -> ActExportStatusResponse:
    """
    Retry export for a specific act.
    
    **Authentication Required:** API Key
    
    Attempts immediate export of the specified act.
    Useful for retrying failed exports.
    """
    # Get act
    stmt = select(ActLegislativ).where(ActLegislativ.id == act_id)
    result = await session.execute(stmt)
    act = result.scalar_one_or_none()
    
    if not act:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act {act_id} not found"
        )
    
    if act.ai_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Act {act_id} has not completed AI processing (status: {act.ai_status})"
        )
    
    # Export immediately
    export_service = ExportService()
    stats = await export_service.export_to_issue_monitoring(
        session=session,
        act_id=act_id,
        limit=1
    )
    
    # Refresh act to get updated data
    await session.refresh(act)
    
    return ActExportStatusResponse(
        id=act.id,
        nr_act=act.nr_act,
        an_act=act.an_act,
        titlu=act.titlu_act,
        export_status=act.export_status,
        export_at=act.export_at.isoformat() if act.export_at else None,
        export_error=act.export_error,
        issue_monitoring_id=act.issue_monitoring_id,
        ai_status=act.ai_status,
        articles_count=len(act.articole) if hasattr(act, 'articole') else 0,
        issues_count=len(act.issues) if hasattr(act, 'issues') else 0
    )


@router.get("/package/{act_id}")
async def preview_export_package(
    act_id: int,
    session: DBSession,
    auth: AuthInfo
) -> dict:
    """
    Preview export package for an act without sending.
    
    **Authentication Required:** API Key
    
    Returns the JSON package that would be sent to Issue Monitoring.
    Useful for debugging and verifying package structure.
    """
    export_service = ExportService()
    packages = await export_service.build_export_package(
        session=session,
        act_id=act_id,
        limit=1
    )
    
    if not packages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No export package found for act {act_id}. "
                   "Check that act exists and has ai_status='completed'."
        )
    
    return packages[0]

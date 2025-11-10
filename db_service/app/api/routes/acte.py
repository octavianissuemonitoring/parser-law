"""
API Routes for Acte Legislative (Legislative Acts).
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status, BackgroundTasks
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, Pagination
from app.models import ActLegislativ, Articol
from app.schemas import (
    ActLegislativCreate,
    ActLegislativUpdate,
    ActLegislativResponse,
    # ActLegislativWithArticole,  # DISABLED due to circular import
    ActLegislativList,
)
from app.services import ImportService

router = APIRouter(prefix="/acte", tags=["Acte Legislative"])


@router.get("", response_model=ActLegislativList)
async def list_acte(
    db: DBSession,
    pagination: Pagination,
    tip_act: Optional[str] = Query(None, description="Filter by act type"),
    an_act: Optional[int] = Query(None, ge=1900, le=2100, description="Filter by year"),
    search: Optional[str] = Query(None, description="Search in title or emitent"),
) -> ActLegislativList:
    """
    List all legislative acts with optional filtering and pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 500)
    - **tip_act**: Filter by act type (e.g., 'LEGE', 'OUG', 'HG')
    - **an_act**: Filter by year
    - **search**: Search in title or emitent fields
    """
    # Build query
    query = select(ActLegislativ)
    
    # Apply filters
    if tip_act:
        query = query.where(ActLegislativ.tip_act == tip_act)
    
    if an_act:
        query = query.where(ActLegislativ.an_act == an_act)
    
    if search:
        search_filter = or_(
            ActLegislativ.titlu_act.ilike(f"%{search}%"),
            ActLegislativ.emitent_act.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    query = query.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(query)
    acte = result.scalars().all()
    
    # Calculate pagination metadata
    page = (pagination.skip // pagination.limit) + 1
    pages = (total + pagination.limit - 1) // pagination.limit  # Ceiling division
    
    return ActLegislativList(
        items=acte,
        total=total,
        page=page,
        size=pagination.limit,
        pages=pages,
    )


@router.get("/{act_id}", response_model=ActLegislativResponse)
async def get_act(act_id: int, db: DBSession) -> ActLegislativResponse:
    """
    Get a specific legislative act by ID.
    
    - **act_id**: The ID of the legislative act
    """
    query = select(ActLegislativ).where(ActLegislativ.id == act_id)
    result = await db.execute(query)
    act = result.scalar_one_or_none()
    
    if not act:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act legislativ cu ID {act_id} nu a fost găsit",
        )
    
    return act


@router.get("/{act_id}/articole", response_model=ActLegislativResponse)
async def get_act_with_articole(act_id: int, db: DBSession) -> ActLegislativResponse:
    """
    Get a legislative act (without nested articole - use /api/v1/articole?act_id=X instead).
    
    - **act_id**: The ID of the legislative act
    """
    query = (
        select(ActLegislativ)
        .where(ActLegislativ.id == act_id)
        # .options(selectinload(ActLegislativ.articole))  # Disabled
    )
    result = await db.execute(query)
    act = result.scalar_one_or_none()
    
    if not act:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act legislativ cu ID {act_id} nu a fost găsit",
        )
    
    return act


@router.post("", response_model=ActLegislativResponse, status_code=status.HTTP_201_CREATED)
async def create_act(act_data: ActLegislativCreate, db: DBSession) -> ActLegislativResponse:
    """
    Create a new legislative act.
    
    - **act_data**: The data for the new legislative act
    """
    # Check if act already exists by URL
    query = select(ActLegislativ).where(ActLegislativ.url_legislatie == act_data.url_legislatie)
    result = await db.execute(query)
    existing_act = result.scalar_one_or_none()
    
    if existing_act:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Act legislativ cu URL {act_data.url_legislatie} există deja (ID: {existing_act.id})",
        )
    
    # Create new act
    new_act = ActLegislativ(**act_data.model_dump())
    db.add(new_act)
    await db.commit()
    await db.refresh(new_act)
    
    return new_act


@router.put("/{act_id}", response_model=ActLegislativResponse)
async def update_act(
    act_id: int,
    act_data: ActLegislativUpdate,
    db: DBSession,
) -> ActLegislativResponse:
    """
    Update an existing legislative act.
    
    - **act_id**: The ID of the legislative act to update
    - **act_data**: The updated data (only provided fields will be updated)
    """
    # Get existing act
    query = select(ActLegislativ).where(ActLegislativ.id == act_id)
    result = await db.execute(query)
    act = result.scalar_one_or_none()
    
    if not act:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act legislativ cu ID {act_id} nu a fost găsit",
        )
    
    # Update fields
    update_data = act_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(act, field, value)
    
    await db.commit()
    await db.refresh(act)
    
    return act


@router.delete("/{act_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_act(act_id: int, db: DBSession) -> None:
    """
    Delete a legislative act and all its articles (CASCADE).
    
    - **act_id**: The ID of the legislative act to delete
    """
    # Get existing act
    query = select(ActLegislativ).where(ActLegislativ.id == act_id)
    result = await db.execute(query)
    act = result.scalar_one_or_none()
    
    if not act:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act legislativ cu ID {act_id} nu a fost găsit",
        )
    
    # Delete act (articles will be deleted automatically via CASCADE)
    await db.delete(act)
    await db.commit()


@router.get("/{act_id}/stats")
async def get_act_stats(act_id: int, db: DBSession) -> dict:
    """
    Get statistics for a legislative act.
    
    - **act_id**: The ID of the legislative act
    """
    # Check if act exists
    query = select(ActLegislativ).where(ActLegislativ.id == act_id)
    result = await db.execute(query)
    act = result.scalar_one_or_none()
    
    if not act:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act legislativ cu ID {act_id} nu a fost găsit",
        )
    
    # Get article statistics
    articole_query = select(Articol).where(Articol.act_id == act_id)
    articole_result = await db.execute(articole_query)
    articole = articole_result.scalars().all()
    
    # Count articles with labels
    articole_with_labels = 0
    for articol in articole:
        if articol.issue or articol.explicatie:
            articole_with_labels += 1
    
    return {
        "act_id": act_id,
        "titlu_act": act.titlu_act,
        "total_articole": len(articole),
        "articole_with_labels": articole_with_labels,
        "label_coverage": round(articole_with_labels / len(articole) * 100, 2) if articole else 0,
    }


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_from_csv(
    db: DBSession,
    rezultate_dir: str = Query("/app/rezultate", description="Path to rezultate directory"),
) -> dict:
    """
    Import legislative acts and articles from CSV files in rezultate directory.
    
    - **rezultate_dir**: Path to directory containing CSV and MD files
    
    This endpoint will:
    1. Scan the rezultate directory for CSV files
    2. For each CSV file, create an ActLegislativ and import all articles
    3. Skip acts that already exist (based on URL)
    4. Return statistics about the import process
    """
    service = ImportService(rezultate_dir)
    stats = await service.import_all_files(db)
    
    return stats

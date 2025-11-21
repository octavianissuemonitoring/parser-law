"""
API Routes for Domenii (Domains/Categories).

Manages thematic domains for legislative acts (e.g., FARMA, TUTUN, DISP_MED).
Acts are assigned to domains when imported, articles can optionally override.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, Pagination
from app.models import Domeniu, ActDomeniu, ArticolDomeniu, ActLegislativ, Articol
from app.schemas import (
    DomeniuCreate,
    DomeniuUpdate,
    DomeniuResponse,
    DomeniuList,
    ActDomeniuAssign,
    ArticolDomeniuAssign,
)

router = APIRouter(prefix="/domenii", tags=["Domenii"])


# ============================================================================
# CRUD Operations for Domenii
# ============================================================================

@router.get("", response_model=DomeniuList)
async def list_domenii(
    db: DBSession,
    pagination: Pagination,
    activ: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in code/name"),
) -> DomeniuList:
    """
    List all domains with optional filtering and pagination.
    
    Returns domains ordered by `ordine` field (lower = displayed first).
    """
    query = select(Domeniu).order_by(Domeniu.ordine, Domeniu.denumire)
    
    # Apply filters
    if activ is not None:
        query = query.where(Domeniu.activ == activ)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Domeniu.cod.ilike(search_pattern)) | 
            (Domeniu.denumire.ilike(search_pattern))
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(pagination.skip).limit(pagination.limit)
    
    # Execute query
    result = await db.execute(query)
    items = result.scalars().all()
    
    return DomeniuList(items=items, total=total)


@router.get("/{domeniu_id}", response_model=DomeniuResponse)
async def get_domeniu(
    domeniu_id: int,
    db: DBSession,
) -> DomeniuResponse:
    """Get a single domain by ID."""
    result = await db.execute(select(Domeniu).where(Domeniu.id == domeniu_id))
    domeniu = result.scalar_one_or_none()
    
    if not domeniu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domeniu with id {domeniu_id} not found"
        )
    
    return domeniu


@router.post("", response_model=DomeniuResponse, status_code=status.HTTP_201_CREATED)
async def create_domeniu(
    domeniu: DomeniuCreate,
    db: DBSession,
) -> DomeniuResponse:
    """
    Create a new domain.
    
    **cod** must be unique (e.g., FARMA, TUTUN).
    """
    # Check if code already exists
    existing = await db.execute(select(Domeniu).where(Domeniu.cod == domeniu.cod))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Domeniu with code '{domeniu.cod}' already exists"
        )
    
    db_domeniu = Domeniu(**domeniu.model_dump())
    db.add(db_domeniu)
    await db.commit()
    await db.refresh(db_domeniu)
    
    return db_domeniu


@router.put("/{domeniu_id}", response_model=DomeniuResponse)
async def update_domeniu(
    domeniu_id: int,
    domeniu: DomeniuUpdate,
    db: DBSession,
) -> DomeniuResponse:
    """Update a domain."""
    result = await db.execute(select(Domeniu).where(Domeniu.id == domeniu_id))
    db_domeniu = result.scalar_one_or_none()
    
    if not db_domeniu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domeniu with id {domeniu_id} not found"
        )
    
    # Check if new code conflicts with existing
    if domeniu.cod and domeniu.cod != db_domeniu.cod:
        existing = await db.execute(select(Domeniu).where(Domeniu.cod == domeniu.cod))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Domeniu with code '{domeniu.cod}' already exists"
            )
    
    # Update fields
    for field, value in domeniu.model_dump(exclude_unset=True).items():
        setattr(db_domeniu, field, value)
    
    await db.commit()
    await db.refresh(db_domeniu)
    
    return db_domeniu


@router.delete("/{domeniu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domeniu(
    domeniu_id: int,
    db: DBSession,
):
    """
    Delete a domain.
    
    **Warning**: This will cascade delete all act-domain and article-domain
    assignments, and all issues linked to this domain.
    """
    result = await db.execute(select(Domeniu).where(Domeniu.id == domeniu_id))
    db_domeniu = result.scalar_one_or_none()
    
    if not db_domeniu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domeniu with id {domeniu_id} not found"
        )
    
    await db.delete(db_domeniu)
    await db.commit()


# ============================================================================
# Act-Domeniu Assignments
# ============================================================================

@router.get("/acte/{act_id}")
async def get_act_domenii(
    act_id: int,
    db: DBSession,
):
    """
    Get all domains assigned to a legislative act.
    
    Returns list of domains with assignment details (relevanta).
    """
    # Verify act exists
    act_result = await db.execute(select(ActLegislativ).where(ActLegislativ.id == act_id))
    if not act_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act with id {act_id} not found"
        )
    
    # Get domains for this act with relevanta
    result = await db.execute(
        select(Domeniu, ActDomeniu.relevanta)
        .join(ActDomeniu, ActDomeniu.domeniu_id == Domeniu.id)
        .where(ActDomeniu.act_id == act_id)
        .order_by(Domeniu.ordine, Domeniu.denumire)
    )
    
    items = []
    for row in result.all():
        domeniu = row[0]
        relevanta = row[1]
        items.append({
            "id": domeniu.id,
            "cod": domeniu.cod,
            "denumire": domeniu.denumire,
            "descriere": domeniu.descriere,
            "culoare": domeniu.culoare,
            "ordine": domeniu.ordine,
            "activ": domeniu.activ,
            "relevanta": relevanta,
        })
    
    return items


@router.put("/acte/{act_id}")
async def replace_act_domenii(
    act_id: int,
    domenii_ids: list[int],
    db: DBSession,
):
    """
    Replace ALL domains for an act with a new set.
    
    This will:
    1. Remove all existing domain assignments
    2. Add the new ones provided
    
    **Request Body:**
    ```json
    [1, 3, 5, 7]
    ```
    
    **Returns:**
    ```json
    {
        "act_id": 1,
        "removed": 3,
        "added": 4,
        "message": "Domains replaced successfully"
    }
    ```
    """
    # Verify act exists
    act_result = await db.execute(select(ActLegislativ).where(ActLegislativ.id == act_id))
    if not act_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act with id {act_id} not found"
        )
    
    # Remove all existing assignments
    delete_result = await db.execute(
        delete(ActDomeniu).where(ActDomeniu.act_id == act_id)
    )
    removed_count = delete_result.rowcount
    
    # Add new assignments
    added_count = 0
    for domeniu_id in domenii_ids:
        # Verify domeniu exists
        domeniu_result = await db.execute(select(Domeniu).where(Domeniu.id == domeniu_id))
        if domeniu_result.scalar_one_or_none():
            db_assignment = ActDomeniu(
                act_id=act_id,
                domeniu_id=domeniu_id,
                relevanta=1.0,  # Default relevance
            )
            db.add(db_assignment)
            added_count += 1
    
    await db.commit()
    
    return {
        "act_id": act_id,
        "removed": removed_count,
        "added": added_count,
        "message": "Domains replaced successfully"
    }


@router.post("/acte/{act_id}/assign", status_code=status.HTTP_201_CREATED)
async def assign_domeniu_to_act(
    act_id: int,
    assignment: ActDomeniuAssign,
    db: DBSession,
):
    """
    Assign a domain to a legislative act.
    
    All articles will inherit this domain unless they have specific overrides.
    """
    # Verify act exists
    act_result = await db.execute(select(ActLegislativ).where(ActLegislativ.id == act_id))
    if not act_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act with id {act_id} not found"
        )
    
    # Verify domeniu exists
    domeniu_result = await db.execute(select(Domeniu).where(Domeniu.id == assignment.domeniu_id))
    if not domeniu_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domeniu with id {assignment.domeniu_id} not found"
        )
    
    # Check if already assigned
    existing = await db.execute(
        select(ActDomeniu).where(
            (ActDomeniu.act_id == act_id) & 
            (ActDomeniu.domeniu_id == assignment.domeniu_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Domeniu {assignment.domeniu_id} already assigned to act {act_id}"
        )
    
    # Create assignment
    db_assignment = ActDomeniu(
        act_id=act_id,
        domeniu_id=assignment.domeniu_id,
        relevanta=assignment.relevanta,
    )
    db.add(db_assignment)
    await db.commit()
    
    return {"message": "Domain assigned to act successfully"}


@router.delete("/acte/{act_id}/unassign/{domeniu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_domeniu_from_act(
    act_id: int,
    domeniu_id: int,
    db: DBSession,
):
    """Remove domain assignment from act."""
    result = await db.execute(
        delete(ActDomeniu).where(
            (ActDomeniu.act_id == act_id) & 
            (ActDomeniu.domeniu_id == domeniu_id)
        )
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment not found"
        )
    
    await db.commit()


# ============================================================================
# Articol-Domeniu Assignments (Overrides)
# ============================================================================

@router.post("/articole/{articol_id}/assign", status_code=status.HTTP_201_CREATED)
async def assign_domeniu_to_articol(
    articol_id: int,
    assignment: ArticolDomeniuAssign,
    db: DBSession,
):
    """
    Assign a domain to a specific article (override).
    
    When set, the article will use these domains instead of inheriting from the parent act.
    """
    # Verify articol exists
    articol_result = await db.execute(select(Articol).where(Articol.id == articol_id))
    if not articol_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Articol with id {articol_id} not found"
        )
    
    # Verify domeniu exists
    domeniu_result = await db.execute(select(Domeniu).where(Domeniu.id == assignment.domeniu_id))
    if not domeniu_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domeniu with id {assignment.domeniu_id} not found"
        )
    
    # Check if already assigned
    existing = await db.execute(
        select(ArticolDomeniu).where(
            (ArticolDomeniu.articol_id == articol_id) & 
            (ArticolDomeniu.domeniu_id == assignment.domeniu_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Domeniu {assignment.domeniu_id} already assigned to articol {articol_id}"
        )
    
    # Create assignment
    db_assignment = ArticolDomeniu(
        articol_id=articol_id,
        domeniu_id=assignment.domeniu_id,
        relevanta=assignment.relevanta,
    )
    db.add(db_assignment)
    await db.commit()
    
    return {"message": "Domain assigned to article successfully (override)"}


@router.delete("/articole/{articol_id}/unassign/{domeniu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_domeniu_from_articol(
    articol_id: int,
    domeniu_id: int,
    db: DBSession,
):
    """Remove domain override from article (will revert to inheriting from act)."""
    result = await db.execute(
        delete(ArticolDomeniu).where(
            (ArticolDomeniu.articol_id == articol_id) & 
            (ArticolDomeniu.domeniu_id == domeniu_id)
        )
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment not found"
        )
    
    await db.commit()

"""
API Routes for Articole (Articles).
"""
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, Pagination
from app.models import Articol, ActLegislativ
from app.schemas import (
    ArticolCreate,
    ArticolUpdate,
    ArticolLabelsUpdate,
    ArticolResponse,
    # ArticolWithAct,  # DISABLED due to circular import
    ArticolList,
    ArticolBatchUpdate,
    ArticolSearchResult,
)

router = APIRouter(prefix="/articole", tags=["Articole"])


@router.get("", response_model=ArticolList)
async def list_articole(
    db: DBSession,
    pagination: Pagination,
    act_id: Optional[int] = Query(None, description="Filter by legislative act ID"),
    issue: Optional[str] = Query(None, description="Filter by issue label"),
    has_labels: Optional[bool] = Query(None, description="Filter articles with/without labels"),
) -> ArticolList:
    """
    List all articles with optional filtering and pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 500)
    - **act_id**: Filter by legislative act ID
    - **issue**: Filter by issue label
    - **has_labels**: Filter articles that have or don't have labels
    """
    # Build query
    query = select(Articol)
    
    # Apply filters
    if act_id:
        query = query.where(Articol.act_id == act_id)
    
    if issue:
        query = query.where(Articol.issue == issue)
    
    if has_labels is not None:
        if has_labels:
            query = query.where(
                or_(
                    Articol.issue.isnot(None),
                    Articol.explicatie.isnot(None),
                )
            )
        else:
            query = query.where(
                Articol.issue.is_(None),
                Articol.explicatie.is_(None),
            )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and order by act_id, ordine
    query = query.order_by(Articol.act_id, Articol.ordine).offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(query)
    articole = result.scalars().all()
    
    # Calculate pagination metadata
    page = (pagination.skip // pagination.limit) + 1
    pages = (total + pagination.limit - 1) // pagination.limit  # Ceiling division
    
    return ArticolList(
        items=articole,
        total=total,
        page=page,
        size=pagination.limit,
        pages=pages,
    )


@router.get("/{articol_id}", response_model=ArticolResponse)
async def get_articol(articol_id: int, db: DBSession) -> ArticolResponse:
    """
    Get a specific article by ID.
    
    - **articol_id**: The ID of the article
    """
    query = select(Articol).where(Articol.id == articol_id)
    result = await db.execute(query)
    articol = result.scalar_one_or_none()
    
    if not articol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Articol cu ID {articol_id} nu a fost găsit",
        )
    
    return articol


@router.get("/{articol_id}/with-act", response_model=ArticolResponse)
async def get_articol_with_act(articol_id: int, db: DBSession) -> ArticolResponse:
    """
    Get an article (without nested act - use GET /api/v1/acte/{act_id} for the parent act).
    
    - **articol_id**: The ID of the article
    """
    query = (
        select(Articol)
        .where(Articol.id == articol_id)
        # .options(selectinload(Articol.act))  # Disabled
    )
    result = await db.execute(query)
    articol = result.scalar_one_or_none()
    
    if not articol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Articol cu ID {articol_id} nu a fost găsit",
        )
    
    return articol


@router.post("", response_model=ArticolResponse, status_code=status.HTTP_201_CREATED)
async def create_articol(articol_data: ArticolCreate, db: DBSession) -> ArticolResponse:
    """
    Create a new article.
    
    - **articol_data**: The data for the new article
    """
    # Check if act exists
    act_query = select(ActLegislativ).where(ActLegislativ.id == articol_data.act_id)
    act_result = await db.execute(act_query)
    act = act_result.scalar_one_or_none()
    
    if not act:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act legislativ cu ID {articol_data.act_id} nu a fost găsit",
        )
    
    # Create new article
    new_articol = Articol(**articol_data.model_dump())
    db.add(new_articol)
    await db.commit()
    await db.refresh(new_articol)
    
    return new_articol


@router.put("/{articol_id}", response_model=ArticolResponse)
async def update_articol(
    articol_id: int,
    articol_data: ArticolUpdate,
    db: DBSession,
) -> ArticolResponse:
    """
    Update an existing article.
    
    - **articol_id**: The ID of the article to update
    - **articol_data**: The updated data (only provided fields will be updated)
    """
    # Get existing article
    query = select(Articol).where(Articol.id == articol_id)
    result = await db.execute(query)
    articol = result.scalar_one_or_none()
    
    if not articol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Articol cu ID {articol_id} nu a fost găsit",
        )
    
    # Update fields
    update_data = articol_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(articol, field, value)
    
    await db.commit()
    await db.refresh(articol)
    
    return articol


@router.patch("/{articol_id}/labels", response_model=ArticolResponse)
async def update_articol_labels(
    articol_id: int,
    labels_data: ArticolLabelsUpdate,
    db: DBSession,
) -> ArticolResponse:
    """
    Update only the LLM labels (issue, explicatie) of an article.
    This is the main endpoint for LLM integration.
    
    - **articol_id**: The ID of the article to update
    - **labels_data**: The label data from LLM
    """
    # Get existing article
    query = select(Articol).where(Articol.id == articol_id)
    result = await db.execute(query)
    articol = result.scalar_one_or_none()
    
    if not articol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Articol cu ID {articol_id} nu a fost găsit",
        )
    
    # Update only labels
    articol.issue = labels_data.issue
    articol.explicatie = labels_data.explicatie
    
    await db.commit()
    await db.refresh(articol)
    
    return articol


@router.post("/batch-update-labels", response_model=dict)
async def batch_update_labels(
    batch_data: ArticolBatchUpdate,
    db: DBSession,
) -> dict:
    """
    Batch update labels for multiple articles.
    Useful for bulk LLM processing.
    
    - **batch_data**: List of article updates with ID and label data
    """
    updated_count = 0
    errors = []
    
    for update_item in batch_data.updates:
        try:
            # Get article
            query = select(Articol).where(Articol.id == update_item["id"])
            result = await db.execute(query)
            articol = result.scalar_one_or_none()
            
            if not articol:
                errors.append(f"Articol cu ID {update_item['id']} nu a fost găsit")
                continue
            
            # Update labels
            if "issue" in update_item:
                articol.issue = update_item["issue"]
            if "explicatie" in update_item:
                articol.explicatie = update_item["explicatie"]
            
            updated_count += 1
            
        except Exception as e:
            errors.append(f"Eroare la actualizarea articolului {update_item.get('id')}: {str(e)}")
    
    await db.commit()
    
    return {
        "updated": updated_count,
        "total": len(batch_data.updates),
        "errors": errors if errors else None,
    }


@router.delete("/{articol_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_articol(articol_id: int, db: DBSession) -> None:
    """
    Delete an article.
    
    - **articol_id**: The ID of the article to delete
    """
    # Get existing article
    query = select(Articol).where(Articol.id == articol_id)
    result = await db.execute(query)
    articol = result.scalar_one_or_none()
    
    if not articol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Articol cu ID {articol_id} nu a fost găsit",
        )
    
    # Delete article
    await db.delete(articol)
    await db.commit()


@router.get("/search/text", response_model=List[ArticolSearchResult])
async def search_articole(
    db: DBSession,
    q: str = Query(..., min_length=3, description="Search query (minimum 3 characters)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
) -> List[ArticolSearchResult]:
    """
    Search articles by content, issue, or explicatie using full-text search.
    
    - **q**: Search query (minimum 3 characters)
    - **limit**: Maximum number of results (default: 50, max: 200)
    """
    # Build search query
    search_filter = or_(
        Articol.text_articol.ilike(f"%{q}%"),
        Articol.issue.ilike(f"%{q}%"),
        Articol.explicatie.ilike(f"%{q}%"),
        Articol.titlu_denumire.ilike(f"%{q}%"),
        Articol.capitol_denumire.ilike(f"%{q}%"),
    )
    
    query = (
        select(Articol)
        .where(search_filter)
        .order_by(Articol.act_id, Articol.ordine)
        .limit(limit)
        .options(selectinload(Articol.act))
    )
    
    result = await db.execute(query)
    articole = result.scalars().all()
    
    # Convert to SearchResult with relevance scoring (basic)
    search_results = []
    for articol in articole:
        # Simple relevance: count occurrences in content
        relevance = 0.0
        q_lower = q.lower()
        if articol.text_articol:
            relevance += articol.text_articol.lower().count(q_lower) * 1.0
        if articol.issue and q_lower in articol.issue.lower():
            relevance += 5.0
        if articol.explicatie and q_lower in articol.explicatie.lower():
            relevance += 3.0
        
        search_results.append(
            ArticolSearchResult(
                **articol.__dict__,
                relevance_score=min(relevance, 100.0),  # Cap at 100
                highlight=articol.text_articol[:200] if articol.text_articol else "",
            )
        )
    
    # Sort by relevance
    search_results.sort(key=lambda x: x.relevance_score, reverse=True)
    
    return search_results

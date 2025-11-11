"""
API Routes for Issues (Quality Problems/Tags).
"""
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func, or_, text
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, Pagination
from app.models import Issue

router = APIRouter(prefix="/issues", tags=["Issues"])


@router.get("")
async def list_issues(
    db: DBSession,
    pagination: Pagination,
    source: Optional[str] = Query(None, description="Filter by source (ai/manual)"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum AI confidence score"),
    search: Optional[str] = Query(None, description="Search in issue name/description"),
) -> Dict[str, Any]:
    """
    List all issues with optional filtering and pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 500)
    - **source**: Filter by source (ai/manual)
    - **min_confidence**: Minimum AI confidence score (0.0-1.0)
    - **search**: Search in issue name and description
    
    Returns:
    ```json
    {
        "items": [
            {
                "id": 1,
                "denumire": "Termen nedefinit: energie regenerabilă",
                "descriere": "Termenul este folosit dar nu este definit clar în text",
                "source": "ai",
                "confidence_score": 0.89,
                "issue_monitoring_id": null,
                "data_creare": "2025-11-10T20:00:00",
                "data_modificare": null
            }
        ],
        "total": 25,
        "skip": 0,
        "limit": 100
    }
    ```
    """
    # Build query
    query = select(Issue).order_by(Issue.data_creare.desc())
    
    # Apply filters
    if source:
        query = query.where(Issue.source == source)
    
    if min_confidence is not None:
        query = query.where(Issue.confidence_score >= min_confidence)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Issue.denumire.ilike(search_pattern),
                Issue.descriere.ilike(search_pattern),
            )
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
    
    # Convert to dict
    items_list = [
        {
            "id": issue.id,
            "denumire": issue.denumire,
            "descriere": issue.descriere,
            "source": issue.source,
            "confidence_score": float(issue.confidence_score) if issue.confidence_score else None,
            "issue_monitoring_id": issue.issue_monitoring_id,
            "data_creare": issue.data_creare.isoformat(),
            "data_modificare": issue.data_modificare.isoformat() if issue.data_modificare else None,
        }
        for issue in items
    ]
    
    return {
        "items": items_list,
        "total": total,
        "skip": pagination.skip,
        "limit": pagination.limit,
    }


@router.get("/{issue_id}")
async def get_issue(
    issue_id: int,
    db: DBSession,
) -> Dict[str, Any]:
    """
    Get a single issue by ID with related entities.
    
    Returns the issue along with counts of related acts, articles, and annexes.
    
    Example response:
    ```json
    {
        "id": 1,
        "denumire": "Termen nedefinit: energie regenerabilă",
        "descriere": "Termenul este folosit dar nu este definit clar în text",
        "source": "ai",
        "confidence_score": 0.89,
        "issue_monitoring_id": null,
        "data_creare": "2025-11-10T20:00:00",
        "data_modificare": null,
        "related_acts_count": 2,
        "related_articles_count": 5,
        "related_annexes_count": 1
    }
    ```
    """
    # Get issue
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with id {issue_id} not found"
        )
    
    # Count related entities (using junction tables)
    # Acts
    acts_count_query = text("""
        SELECT COUNT(*) FROM legislatie.acte_issues 
        WHERE issue_id = :issue_id
    """)
    acts_result = await db.execute(acts_count_query, {"issue_id": issue_id})
    acts_count = acts_result.scalar() or 0
    
    # Articles
    articles_count_query = text("""
        SELECT COUNT(*) FROM legislatie.articole_issues 
        WHERE issue_id = :issue_id
    """)
    articles_result = await db.execute(articles_count_query, {"issue_id": issue_id})
    articles_count = articles_result.scalar() or 0
    
    # Annexes
    annexes_count_query = text("""
        SELECT COUNT(*) FROM legislatie.anexe_issues 
        WHERE issue_id = :issue_id
    """)
    annexes_result = await db.execute(annexes_count_query, {"issue_id": issue_id})
    annexes_count = annexes_result.scalar() or 0
    
    return {
        "id": issue.id,
        "denumire": issue.denumire,
        "descriere": issue.descriere,
        "source": issue.source,
        "confidence_score": float(issue.confidence_score) if issue.confidence_score else None,
        "issue_monitoring_id": issue.issue_monitoring_id,
        "data_creare": issue.data_creare.isoformat(),
        "data_modificare": issue.data_modificare.isoformat() if issue.data_modificare else None,
        "related_acts_count": acts_count,
        "related_articles_count": articles_count,
        "related_annexes_count": annexes_count,
    }

"""
API Routes for Issues (Quality Problems/Tags).

Extended to support Tier 1 (direct) and Tier 2 (structure) issue assignments
with mandatory domain context.
"""
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func, or_, text, delete
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, Pagination
from app.models import (
    Issue, 
    ArticolIssue, 
    ActIssue, 
    AnexaIssue, 
    StructureIssue,
    Articol,
    ActLegislativ,
    Anexa,
    Domeniu,
)
from app.schemas import (
    IssueCreate,
    IssueUpdate,
    IssueResponse,
    IssueLinkCreate,
    IssueLinkResponse,
    IssueUnlink,
    StructureIssueLinkCreate,
    StructureIssueLinkResponse,
    StructureIssueUnlink,
)

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


# ============================================================================
# CRUD Operations for Issues
# ============================================================================

@router.post("", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
async def create_issue(
    issue: IssueCreate,
    db: DBSession,
) -> IssueResponse:
    """
    Create a new issue.
    
    Issues can be created by AI processing or manually by users.
    """
    db_issue = Issue(**issue.model_dump())
    db.add(db_issue)
    await db.commit()
    await db.refresh(db_issue)
    
    return db_issue


@router.put("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    issue: IssueUpdate,
    db: DBSession,
) -> IssueResponse:
    """Update an existing issue."""
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    db_issue = result.scalar_one_or_none()
    
    if not db_issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with id {issue_id} not found"
        )
    
    # Update fields
    for field, value in issue.model_dump(exclude_unset=True).items():
        setattr(db_issue, field, value)
    
    await db.commit()
    await db.refresh(db_issue)
    
    return db_issue


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(
    issue_id: int,
    db: DBSession,
):
    """
    Delete an issue.
    
    **Warning**: This will cascade delete all links to documents (articles, acts, annexes, structures).
    """
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    db_issue = result.scalar_one_or_none()
    
    if not db_issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with id {issue_id} not found"
        )
    
    await db.delete(db_issue)
    await db.commit()


# ============================================================================
# TIER 1: Link/Unlink Issues to Documents (articol/act/anexa)
# ============================================================================

@router.post("/link", response_model=IssueLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_issue_to_document(
    link: IssueLinkCreate,
    db: DBSession,
) -> IssueLinkResponse:
    """
    Link an issue to a document (Tier 1: Direct assignment).
    
    Supported document types: articol, act, anexa.
    Domain context is MANDATORY - issues are always contextualized.
    
    Example for AI service:
    ```json
    {
        "document_type": "articol",
        "document_id": 123,
        "issue_id": 42,
        "domeniu_id": 1,
        "relevance_score": 0.95
    }
    ```
    """
    # Verify domeniu exists
    domeniu_result = await db.execute(select(Domeniu).where(Domeniu.id == link.domeniu_id))
    if not domeniu_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domeniu with id {link.domeniu_id} not found"
        )
    
    # Verify issue exists
    issue_result = await db.execute(select(Issue).where(Issue.id == link.issue_id))
    if not issue_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with id {link.issue_id} not found"
        )
    
    # Handle based on document type
    if link.document_type == "articol":
        # Verify articol exists
        doc_result = await db.execute(select(Articol).where(Articol.id == link.document_id))
        if not doc_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Articol with id {link.document_id} not found"
            )
        
        # Check if already linked
        existing = await db.execute(
            select(ArticolIssue).where(
                (ArticolIssue.articol_id == link.document_id) &
                (ArticolIssue.issue_id == link.issue_id) &
                (ArticolIssue.domeniu_id == link.domeniu_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Issue already linked to this articol in this domain"
            )
        
        # Create link
        db_link = ArticolIssue(
            articol_id=link.document_id,
            issue_id=link.issue_id,
            domeniu_id=link.domeniu_id,
            relevance_score=link.relevance_score,
        )
        db.add(db_link)
        await db.commit()
        await db.refresh(db_link)
        
        return IssueLinkResponse(
            id=db_link.id,
            document_type="articol",
            document_id=db_link.articol_id,
            issue_id=db_link.issue_id,
            domeniu_id=db_link.domeniu_id,
            relevance_score=float(db_link.relevance_score) if db_link.relevance_score else None,
            added_at=db_link.added_at,
        )
    
    elif link.document_type == "act":
        # Verify act exists
        doc_result = await db.execute(select(ActLegislativ).where(ActLegislativ.id == link.document_id))
        if not doc_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Act with id {link.document_id} not found"
            )
        
        # Check if already linked
        existing = await db.execute(
            select(ActIssue).where(
                (ActIssue.act_id == link.document_id) &
                (ActIssue.issue_id == link.issue_id) &
                (ActIssue.domeniu_id == link.domeniu_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Issue already linked to this act in this domain"
            )
        
        # Create link
        db_link = ActIssue(
            act_id=link.document_id,
            issue_id=link.issue_id,
            domeniu_id=link.domeniu_id,
            relevance_score=link.relevance_score,
        )
        db.add(db_link)
        await db.commit()
        await db.refresh(db_link)
        
        return IssueLinkResponse(
            id=db_link.id,
            document_type="act",
            document_id=db_link.act_id,
            issue_id=db_link.issue_id,
            domeniu_id=db_link.domeniu_id,
            relevance_score=float(db_link.relevance_score) if db_link.relevance_score else None,
            added_at=db_link.added_at,
        )
    
    elif link.document_type == "anexa":
        # Verify anexa exists
        doc_result = await db.execute(select(Anexa).where(Anexa.id == link.document_id))
        if not doc_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Anexa with id {link.document_id} not found"
            )
        
        # Check if already linked
        existing = await db.execute(
            select(AnexaIssue).where(
                (AnexaIssue.anexa_id == link.document_id) &
                (AnexaIssue.issue_id == link.issue_id) &
                (AnexaIssue.domeniu_id == link.domeniu_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Issue already linked to this anexa in this domain"
            )
        
        # Create link
        db_link = AnexaIssue(
            anexa_id=link.document_id,
            issue_id=link.issue_id,
            domeniu_id=link.domeniu_id,
            relevance_score=link.relevance_score,
        )
        db.add(db_link)
        await db.commit()
        await db.refresh(db_link)
        
        return IssueLinkResponse(
            id=db_link.id,
            document_type="anexa",
            document_id=db_link.anexa_id,
            issue_id=db_link.issue_id,
            domeniu_id=db_link.domeniu_id,
            relevance_score=float(db_link.relevance_score) if db_link.relevance_score else None,
            added_at=db_link.added_at,
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document_type: {link.document_type}"
        )


@router.delete("/unlink", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_issue_from_document(
    unlink: IssueUnlink,
    db: DBSession,
):
    """
    Unlink an issue from a document.
    
    Removes the Tier 1 link between issue and document in specified domain.
    """
    if unlink.document_type == "articol":
        result = await db.execute(
            delete(ArticolIssue).where(
                (ArticolIssue.articol_id == unlink.document_id) &
                (ArticolIssue.issue_id == unlink.issue_id) &
                (ArticolIssue.domeniu_id == unlink.domeniu_id)
            )
        )
    elif unlink.document_type == "act":
        result = await db.execute(
            delete(ActIssue).where(
                (ActIssue.act_id == unlink.document_id) &
                (ActIssue.issue_id == unlink.issue_id) &
                (ActIssue.domeniu_id == unlink.domeniu_id)
            )
        )
    elif unlink.document_type == "anexa":
        result = await db.execute(
            delete(AnexaIssue).where(
                (AnexaIssue.anexa_id == unlink.document_id) &
                (AnexaIssue.issue_id == unlink.issue_id) &
                (AnexaIssue.domeniu_id == unlink.domeniu_id)
            )
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document_type: {unlink.document_type}"
        )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link not found"
        )
    
    await db.commit()


# ============================================================================
# TIER 2: Link/Unlink Issues to Structure (titlu/capitol/sectiune)
# ============================================================================

@router.post("/link-structure", response_model=StructureIssueLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_issue_to_structure(
    link: StructureIssueLinkCreate,
    db: DBSession,
) -> StructureIssueLinkResponse:
    """
    Link an issue to a structural element (Tier 2: Parent-level assignment).
    
    Structure types: titlu, capitol, sectiune.
    These issues are displayed in the UI tree at the structure level
    and apply thematically to all child articles.
    
    Example:
    ```json
    {
        "act_id": 1,
        "structure_type": "capitol",
        "issue_id": 42,
        "domeniu_id": 1,
        "capitol_nr": "3",
        "capitol_denumire": "Sancțiuni administrative",
        "relevance_score": 0.88
    }
    ```
    """
    # Verify act exists
    act_result = await db.execute(select(ActLegislativ).where(ActLegislativ.id == link.act_id))
    if not act_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Act with id {link.act_id} not found"
        )
    
    # Verify domeniu exists
    domeniu_result = await db.execute(select(Domeniu).where(Domeniu.id == link.domeniu_id))
    if not domeniu_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domeniu with id {link.domeniu_id} not found"
        )
    
    # Verify issue exists
    issue_result = await db.execute(select(Issue).where(Issue.id == link.issue_id))
    if not issue_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with id {link.issue_id} not found"
        )
    
    # Check if already linked
    existing = await db.execute(
        select(StructureIssue).where(
            (StructureIssue.act_id == link.act_id) &
            (StructureIssue.structure_type == link.structure_type) &
            (StructureIssue.titlu_nr == link.titlu_nr) &
            (StructureIssue.capitol_nr == link.capitol_nr) &
            (StructureIssue.sectiune_nr == link.sectiune_nr) &
            (StructureIssue.issue_id == link.issue_id) &
            (StructureIssue.domeniu_id == link.domeniu_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Issue already linked to this structure in this domain"
        )
    
    # Create link
    db_link = StructureIssue(
        act_id=link.act_id,
        structure_type=link.structure_type,
        titlu_nr=link.titlu_nr,
        titlu_denumire=link.titlu_denumire,
        capitol_nr=link.capitol_nr,
        capitol_denumire=link.capitol_denumire,
        sectiune_nr=link.sectiune_nr,
        sectiune_denumire=link.sectiune_denumire,
        issue_id=link.issue_id,
        domeniu_id=link.domeniu_id,
        relevance_score=link.relevance_score,
    )
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    
    return StructureIssueLinkResponse(
        id=db_link.id,
        act_id=db_link.act_id,
        structure_type=db_link.structure_type,
        issue_id=db_link.issue_id,
        domeniu_id=db_link.domeniu_id,
        relevance_score=float(db_link.relevance_score) if db_link.relevance_score else None,
        added_at=db_link.added_at,
    )


@router.delete("/unlink-structure", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_issue_from_structure(
    unlink: StructureIssueUnlink,
    db: DBSession,
):
    """
    Unlink an issue from a structural element.
    
    Removes the Tier 2 link between issue and structure in specified domain.
    """
    result = await db.execute(
        delete(StructureIssue).where(
            (StructureIssue.act_id == unlink.act_id) &
            (StructureIssue.structure_type == unlink.structure_type) &
            (StructureIssue.titlu_nr == unlink.titlu_nr) &
            (StructureIssue.capitol_nr == unlink.capitol_nr) &
            (StructureIssue.sectiune_nr == unlink.sectiune_nr) &
            (StructureIssue.issue_id == unlink.issue_id) &
            (StructureIssue.domeniu_id == unlink.domeniu_id)
        )
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Structure link not found"
        )
    
    await db.commit()

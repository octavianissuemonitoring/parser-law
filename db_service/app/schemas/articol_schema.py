"""
Pydantic schemas for Articol.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING, Literal
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.issue_schema import IssueWithContext
from app.schemas.domeniu_schema import DomeniuWithSource

if TYPE_CHECKING:
    from app.schemas.act_schema import ActLegislativResponse


# AI Status type
AIStatusType = Literal[0, 1, 2, 9]  # 0=not_processed, 1=processing, 2=processed, 9=error


# Base schema - common fields
class ArticolBase(BaseModel):
    """Base schema for Articol."""
    
    articol_nr: Optional[str] = Field(None, max_length=20, description="Număr articol")
    articol_label: Optional[str] = Field(None, max_length=50, description="Label articol")
    
    # Structură ierarhică
    titlu_nr: Optional[int] = Field(None, description="Număr titlu")
    titlu_denumire: Optional[str] = Field(None, description="Denumire titlu")
    capitol_nr: Optional[int] = Field(None, description="Număr capitol")
    capitol_denumire: Optional[str] = Field(None, description="Denumire capitol")
    sectiune_nr: Optional[int] = Field(None, description="Număr secțiune")
    sectiune_denumire: Optional[str] = Field(None, description="Denumire secțiune")
    subsectiune_nr: Optional[int] = Field(None, description="Număr subsecțiune")
    subsectiune_denumire: Optional[str] = Field(None, description="Denumire subsecțiune")
    
    # Conținut
    text_articol: str = Field(..., description="Text complet articol")
    
    # LLM Labels (DEPRECATED - use issues system instead)
    # Note: 'issue' field removed from database - now using articole_issues junction
    explicatie: Optional[str] = Field(None, description="Explicație (generat LLM) - DEPRECATED, use metadate")
    
    # Metadata
    ordine: Optional[int] = Field(None, description="Ordinea în act")


# Schema for creating new Articol
class ArticolCreate(ArticolBase):
    """Schema for creating a new Articol."""
    
    act_id: int = Field(..., description="ID act legislativ")


# Schema for updating Articol
class ArticolUpdate(BaseModel):
    """Schema for updating an Articol (all fields optional)."""
    
    articol_nr: Optional[str] = Field(None, max_length=20)
    articol_label: Optional[str] = Field(None, max_length=50)
    titlu_nr: Optional[int] = None
    titlu_denumire: Optional[str] = None
    capitol_nr: Optional[int] = None
    capitol_denumire: Optional[str] = None
    sectiune_nr: Optional[int] = None
    sectiune_denumire: Optional[str] = None
    subsectiune_nr: Optional[int] = None
    subsectiune_denumire: Optional[str] = None
    text_articol: Optional[str] = None
    explicatie: Optional[str] = None  # DEPRECATED
    ordine: Optional[int] = None
    
    # AI processing fields
    ai_status: Optional[AIStatusType] = Field(None, description="AI status: 0=not_processed, 1=processing, 2=processed, 9=error")
    ai_status_message: Optional[str] = Field(None, description="Optional message explaining status (error details, notes, etc)")
    metadate: Optional[str] = Field(None, description="AI-generated metadata/summary")


# Schema for updating labels only (for LLM integration) - DEPRECATED
class ArticolLabelsUpdate(BaseModel):
    """Schema for updating only explicatie. NOTE: 'issue' field removed - use issues API."""
    
    explicatie: Optional[str] = Field(None, description="Explicație")


# Schema for response (includes ID and timestamps)
class ArticolResponse(ArticolBase):
    """Schema for Articol response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    act_id: int
    ai_status: int = Field(default=0, description="AI processing status")
    ai_processed_at: Optional[datetime] = Field(None, description="When AI processing completed")
    ai_status_message: Optional[str] = Field(None, description="Optional status message")
    metadate: Optional[str] = Field(None, description="AI-generated summary")
    created_at: datetime
    updated_at: datetime


# # Schema with Act info included - DISABLED due to circular import
# class ArticolWithAct(ArticolResponse):
#     """Schema for Articol with Act info."""
#     
#     act: "ActLegislativResponse"


# Schema for batch update
class ArticolBatchUpdate(BaseModel):
    """Schema for batch updating articole."""
    
    updates: list[dict] = Field(..., description="List of {id, issue, explicatie}")


# Schema for list/search responses
class ArticolList(BaseModel):
    """Schema for paginated Articol list."""
    
    items: list[ArticolResponse]
    total: int
    page: int
    size: int
    pages: int


# Schema for search result with relevance
class ArticolSearchResult(ArticolResponse):
    """Schema for search results with relevance score."""
    
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Search relevance")
    highlight: Optional[str] = Field(None, description="Highlighted text snippet")


# ============================================================================
# Enhanced Response Schemas with Issues and Domenii
# ============================================================================

class ArticolWithIssues(ArticolResponse):
    """Article response with Tier 1 issues (direct issues only)."""
    
    issues: list[IssueWithContext] = Field(
        default_factory=list, 
        description="Tier 1 issues linked directly to this article"
    )
    domenii: list[DomeniuWithSource] = Field(
        default_factory=list,
        description="Effective domains (from article override or inherited from act)"
    )


class ArticolWithFullContext(ArticolWithIssues):
    """Article with complete context: issues, domains, and AI status."""
    
    # AI status is already in ArticolResponse, just keeping for clarity
    pass


# ============================================================================
# AI Service Integration Schemas
# ============================================================================

class ArticolAIStatusUpdate(BaseModel):
    """Schema for AI service to update article processing status."""
    
    article_ids: list[int] = Field(..., description="List of article IDs to update")
    ai_status: AIStatusType = Field(..., description="New AI status: 0=not_processed, 1=processing, 2=processed, 9=error")
    ai_status_message: Optional[str] = Field(None, description="Optional message (error details, processing notes, etc)")
    metadate: Optional[str] = Field(None, description="AI-generated summary (when status=2)")


class ArticolAIBatchResponse(BaseModel):
    """Response for batch AI status updates."""
    
    success: bool
    updated_count: int
    failed_ids: list[int] = Field(default_factory=list)
    message: str

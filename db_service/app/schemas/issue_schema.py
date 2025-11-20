"""
Pydantic schemas for Issues and Issues-Document relationships.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.domeniu_schema import DomeniuMinimal


# ============================================================================
# Issue Base Schemas
# ============================================================================

class IssueBase(BaseModel):
    """Base schema for Issue."""
    
    denumire: str = Field(..., max_length=256, description="Issue title/name (max 256 chars)")
    descriere: Optional[str] = Field(None, description="Detailed description")
    source: Optional[str] = Field(default="ai", max_length=20, description="Source: 'ai' or 'manual'")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence (0.00-1.00)")


class IssueCreate(IssueBase):
    """Schema for creating a new Issue."""
    pass


class IssueUpdate(BaseModel):
    """Schema for updating an Issue (all fields optional)."""
    
    denumire: Optional[str] = Field(None, max_length=256)
    descriere: Optional[str] = None
    source: Optional[str] = Field(None, max_length=20)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class IssueResponse(IssueBase):
    """Schema for Issue response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    issue_monitoring_id: Optional[int] = None
    data_creare: datetime
    data_modificare: Optional[datetime] = None


class IssueMinimal(BaseModel):
    """Minimal Issue info for embedding in document responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    denumire: str
    descriere: Optional[str] = None
    confidence_score: Optional[float] = None


# ============================================================================
# Issue-Document Link Schemas (Tier 1: Direct Issues)
# ============================================================================

class IssueLinkCreate(BaseModel):
    """Schema for linking an issue to a document (Tier 1)."""
    
    document_type: Literal["articol", "act", "anexa"] = Field(
        ..., 
        description="Document type to link to"
    )
    document_id: int = Field(..., description="Document ID")
    issue_id: int = Field(..., description="Issue ID")
    domeniu_id: int = Field(..., description="Domain ID (MANDATORY - issues are always contextualized)")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI relevance score (0.00-1.00)")


class IssueLinkResponse(BaseModel):
    """Response after linking issue to document."""
    
    id: int
    document_type: str
    document_id: int
    issue_id: int
    domeniu_id: int
    relevance_score: Optional[float] = None
    added_at: datetime


class IssueUnlink(BaseModel):
    """Schema for unlinking an issue from a document."""
    
    document_type: Literal["articol", "act", "anexa"] = Field(..., description="Document type")
    document_id: int = Field(..., description="Document ID")
    issue_id: int = Field(..., description="Issue ID")
    domeniu_id: int = Field(..., description="Domain ID")


# ============================================================================
# Structure Issue Schemas (Tier 2: Hierarchical Issues)
# ============================================================================

class StructureIssueLinkCreate(BaseModel):
    """Schema for linking an issue to a structural element (Tier 2)."""
    
    act_id: int = Field(..., description="Act ID")
    structure_type: Literal["titlu", "capitol", "sectiune"] = Field(
        ..., 
        description="Structure type: titlu, capitol, or sectiune"
    )
    issue_id: int = Field(..., description="Issue ID")
    domeniu_id: int = Field(..., description="Domain ID (MANDATORY)")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance score")
    
    # Structure identifiers (provide appropriate field based on structure_type)
    titlu_nr: Optional[str] = Field(None, max_length=50, description="Title number (e.g., 'I', 'II')")
    titlu_denumire: Optional[str] = Field(None, description="Title name")
    capitol_nr: Optional[str] = Field(None, max_length=50, description="Chapter number (e.g., '1', '2')")
    capitol_denumire: Optional[str] = Field(None, description="Chapter name")
    sectiune_nr: Optional[str] = Field(None, max_length=50, description="Section number")
    sectiune_denumire: Optional[str] = Field(None, description="Section name")


class StructureIssueLinkResponse(BaseModel):
    """Response after linking issue to structure."""
    
    id: int
    act_id: int
    structure_type: str
    issue_id: int
    domeniu_id: int
    relevance_score: Optional[float] = None
    added_at: datetime


class StructureIssueUnlink(BaseModel):
    """Schema for unlinking issue from structure."""
    
    act_id: int
    structure_type: Literal["titlu", "capitol", "sectiune"]
    issue_id: int
    domeniu_id: int
    titlu_nr: Optional[str] = None
    capitol_nr: Optional[str] = None
    sectiune_nr: Optional[str] = None


# ============================================================================
# Issue with Context (for responses)
# ============================================================================

class IssueWithContext(IssueMinimal):
    """Issue with domain context and relevance for embedding in document responses."""
    
    domeniu: DomeniuMinimal
    relevance_score: Optional[float] = None
    tier: Literal[1, 2] = Field(..., description="Tier 1 (direct) or Tier 2 (structure)")


class IssuesByDomain(BaseModel):
    """Issues grouped by domain for a document."""
    
    domeniu: DomeniuMinimal
    tier1_issues: list[IssueMinimal] = Field(default_factory=list, description="Direct issues")
    tier2_issues: list[IssueMinimal] = Field(default_factory=list, description="Inherited structure issues")

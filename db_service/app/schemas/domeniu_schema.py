"""
Pydantic schemas for Domenii (Domains/Categories).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Base schema - common fields
class DomeniuBase(BaseModel):
    """Base schema for Domeniu."""
    
    cod: str = Field(..., max_length=50, description="Unique code (e.g., FARMA, TUTUN)")
    denumire: str = Field(..., max_length=255, description="Display name")
    descriere: Optional[str] = Field(None, description="Detailed description")
    culoare: Optional[str] = Field(None, max_length=7, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color (e.g., #3B82F6)")
    ordine: int = Field(default=0, description="Display order (lower = first)")
    activ: bool = Field(default=True, description="Active status")


# Schema for creating new Domeniu
class DomeniuCreate(DomeniuBase):
    """Schema for creating a new Domeniu."""
    pass


# Schema for updating Domeniu
class DomeniuUpdate(BaseModel):
    """Schema for updating a Domeniu (all fields optional)."""
    
    cod: Optional[str] = Field(None, max_length=50)
    denumire: Optional[str] = Field(None, max_length=255)
    descriere: Optional[str] = None
    culoare: Optional[str] = Field(None, max_length=7, pattern="^#[0-9A-Fa-f]{6}$")
    ordine: Optional[int] = None
    activ: Optional[bool] = None


# Schema for response (includes ID and timestamps)
class DomeniuResponse(DomeniuBase):
    """Schema for Domeniu response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# Minimal schema for embedding in other responses
class DomeniuMinimal(BaseModel):
    """Minimal Domeniu info for embedding."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cod: str
    denumire: str
    culoare: Optional[str] = None


# Schema for list response
class DomeniuList(BaseModel):
    """List of Domenii."""
    
    items: list[DomeniuResponse]
    total: int


# ============================================================================
# Schemas for Act-Domeniu and Articol-Domeniu assignments
# ============================================================================

class ActDomeniuAssign(BaseModel):
    """Schema for assigning domains to an act."""
    
    domeniu_id: int = Field(..., description="Domain ID to assign")
    relevanta: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance score (0.00-1.00)")


class ArticolDomeniuAssign(BaseModel):
    """Schema for assigning domains to an article (override)."""
    
    domeniu_id: int = Field(..., description="Domain ID to assign")
    relevanta: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance score (0.00-1.00)")


class DomeniuWithSource(DomeniuMinimal):
    """Domain with source indicator (for inheritance display)."""
    
    source: str = Field(..., description="Source: 'act' (inherited) or 'articol' (override)")

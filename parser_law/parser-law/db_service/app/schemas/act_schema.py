"""
Pydantic schemas for Act Legislativ.
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Base schema - common fields
class ActLegislativBase(BaseModel):
    """Base schema for Act Legislativ."""
    
    tip_act: str = Field(..., max_length=50, description="Tip act (LEGE, ORDONANȚĂ, etc.)")
    nr_act: Optional[str] = Field(None, max_length=50, description="Număr act")
    data_act: Optional[date] = Field(None, description="Data promulgării")
    an_act: Optional[int] = Field(None, description="Anul actului")
    titlu_act: str = Field(..., description="Titlul complet al actului")
    emitent_act: Optional[str] = Field(None, max_length=255, description="Emitent act")
    mof_nr: Optional[str] = Field(None, max_length=50, description="Număr Monitorul Oficial")
    mof_data: Optional[date] = Field(None, description="Data publicare MOF")
    mof_an: Optional[int] = Field(None, description="Anul MOF")
    url_legislatie: Optional[str] = Field(None, description="URL legislatie.just.ro")
    html_content: Optional[str] = Field(None, description="HTML original (opțional)")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Parsing confidence")


# Schema for creating new Act
class ActLegislativCreate(ActLegislativBase):
    """Schema for creating a new Act Legislativ."""
    pass


# Schema for updating Act
class ActLegislativUpdate(BaseModel):
    """Schema for updating an Act Legislativ (all fields optional)."""
    
    tip_act: Optional[str] = Field(None, max_length=50)
    nr_act: Optional[str] = Field(None, max_length=50)
    data_act: Optional[date] = None
    an_act: Optional[int] = None
    titlu_act: Optional[str] = None
    emitent_act: Optional[str] = Field(None, max_length=255)
    mof_nr: Optional[str] = Field(None, max_length=50)
    mof_data: Optional[date] = None
    mof_an: Optional[int] = None
    url_legislatie: Optional[str] = None
    html_content: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


# Schema for response (includes ID and timestamps)
class ActLegislativResponse(ActLegislativBase):
    """Schema for Act Legislativ response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Computed fields (if articole are loaded)
    articole_count: Optional[int] = Field(None, description="Number of articles")


# Schema with articole included
class ActLegislativWithArticole(ActLegislativResponse):
    """Schema for Act Legislativ with articole."""
    
    from app.schemas.articol_schema import ArticolResponse
    
    articole: list[ArticolResponse] = Field(default_factory=list)


# Schema for list/search responses
class ActLegislativList(BaseModel):
    """Schema for paginated Act Legislativ list."""
    
    items: list[ActLegislativResponse]
    total: int
    page: int
    size: int
    pages: int

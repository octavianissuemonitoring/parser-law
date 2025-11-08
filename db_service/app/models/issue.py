"""
SQLAlchemy model for Issue (Problems/Tags extracted by AI).
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Text, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Issue(Base):
    """
    Model pentru issues/probleme identificate în legislație.
    
    Issues sunt extrase automat de AI sau adăugate manual,
    și pot fi asociate cu acte, articole sau anexe.
    """
    
    __tablename__ = "issues"
    __table_args__ = {"schema": "legislatie"}
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Issue Details
    denumire: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        index=True,
        comment="Issue title/name (max 256 chars)"
    )
    descriere: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the issue"
    )
    
    # AI Metadata
    source: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        default="ai",
        comment="Source: 'ai' (extracted) or 'manual' (user-added)"
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        nullable=True,
        comment="AI confidence score (0.00-1.00)"
    )
    
    # Export to Issue Monitoring
    issue_monitoring_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
        index=True,
        comment="ID in Issue Monitoring database after export"
    )
    
    # Timestamps
    data_creare: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    data_modificare: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now()
    )
    
    # Relationships
    acte: Mapped[List["ActLegislativ"]] = relationship(
        "ActLegislativ",
        secondary="legislatie.acte_issues",
        back_populates="issues",
        lazy="selectin"
    )
    
    articole: Mapped[List["Articol"]] = relationship(
        "Articol",
        secondary="legislatie.articole_issues",
        back_populates="issues",
        lazy="selectin"
    )
    
    anexe: Mapped[List["Anexa"]] = relationship(
        "Anexa",
        secondary="legislatie.anexe_issues",
        back_populates="issues",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Issue(id={self.id}, denumire='{self.denumire[:50]}', source={self.source})>"
    
    @property
    def is_ai_generated(self) -> bool:
        """Check if issue was extracted by AI."""
        return self.source == "ai"
    
    @property
    def is_exported(self) -> bool:
        """Check if issue has been exported to Issue Monitoring."""
        return self.issue_monitoring_id is not None

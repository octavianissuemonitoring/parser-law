"""
SQLAlchemy model for Anexa (Annex/Attachment to Legislative Acts).
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Anexa(Base):
    """
    Model pentru anexele actelor legislative.
    
    Anexele sunt separate de articole și pot avea propriile lor
    issues și metadate generate de AI.
    """
    
    __tablename__ = "anexe"
    __table_args__ = (
        UniqueConstraint("act_id", "ordine", name="unique_anexa_per_act"),
        {"schema": "legislatie"}
    )
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    act_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.acte_legislative.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to parent legislative act"
    )
    
    # Anexa Details
    anexa_nr: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Annex number/identifier (e.g., 'Anexa 1', 'Anexa A')"
    )
    ordine: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Order/sequence number for sorting"
    )
    titlu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Annex title/description"
    )
    continut: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Annex content (text or structured data)"
    )
    
    # AI Metadata
    metadate: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI-generated summary/explanation"
    )
    
    # AI Processing Status
    ai_status: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        default="pending",
        comment="AI processing status: pending, processing, completed, error"
    )
    ai_processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when AI processing completed"
    )
    ai_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI processing error message if any"
    )
    
    # Export to Issue Monitoring
    issue_monitoring_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="ID in Issue Monitoring database after export"
    )
    
    # Timestamps
    data_creare: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships to junction tables
    anexe_issues: Mapped[List["AnexaIssue"]] = relationship(
        "AnexaIssue",
        back_populates="anexa",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    data_modificare: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now()
    )
    
    # Relationships
    act: Mapped["ActLegislativ"] = relationship(
        "ActLegislativ",
        back_populates="anexe",
        lazy="selectin"
    )
    
    # TODO: Uncomment when anexe_issues table is created via migration
    # issues: Mapped[List["Issue"]] = relationship(
    #     "Issue",
    #     secondary="legislatie.anexe_issues",
    #     back_populates="anexe",
    #     lazy="selectin"
    # )
    
    def __repr__(self) -> str:
        return f"<Anexa(id={self.id}, act_id={self.act_id}, nr={self.anexa_nr}, ordine={self.ordine})>"
    
    @property
    def display_name(self) -> str:
        """Generate display name for the anexa."""
        if self.anexa_nr:
            return self.anexa_nr
        return f"Anexa {self.ordine}"
    
    @property
    def is_processed(self) -> bool:
        """Check if AI processing is completed."""
        return self.ai_status == "completed"
    
    @property
    def is_exported(self) -> bool:
        """Check if anexa has been exported to Issue Monitoring."""
        return self.issue_monitoring_id is not None

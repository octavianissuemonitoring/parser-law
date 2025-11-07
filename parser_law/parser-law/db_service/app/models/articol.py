"""
SQLAlchemy model for Articol (Article).
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.act_legislativ import ActLegislativ


class Articol(Base):
    """
    Model pentru articolele din actele legislative.
    
    Fiecare articol aparține unui act legislativ și conține:
    - Structură ierarhică (titlu, capitol, secțiune)
    - Conținut text
    - Labels generate de LLM (issue, explicatie)
    """
    
    __tablename__ = "articole"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key to ActLegislativ
    act_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acte_legislative.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Identificare Articol
    articol_nr: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    articol_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Structură Ierarhică
    titlu_nr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    titlu_denumire: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    capitol_nr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    capitol_denumire: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    sectiune_nr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sectiune_denumire: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    subsectiune_nr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    subsectiune_denumire: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Conținut
    text_articol: Mapped[str] = mapped_column(Text, nullable=False)
    
    # LLM Generated Labels (editabile)
    issue: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explicatie: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    ordine: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Order of article in the act (1, 2, 3...)"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    act: Mapped["ActLegislativ"] = relationship(
        "ActLegislativ",
        back_populates="articole",
        lazy="selectin"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_articole_act_ordine", "act_id", "ordine"),
        Index("idx_articole_act_nr", "act_id", "articol_nr"),
        # Full-text search indexes (created in migration)
        # Index("idx_articole_issue_fts", text("to_tsvector('romanian', issue)"), postgresql_using="gin"),
        # Index("idx_articole_text_fts", text("to_tsvector('romanian', text_articol)"), postgresql_using="gin"),
        {"schema": "legislatie"}
    )
    
    def __repr__(self) -> str:
        return f"<Articol(id={self.id}, act_id={self.act_id}, nr={self.articol_nr})>"
    
    @property
    def display_name(self) -> str:
        """Generate display name for the article."""
        if self.articol_label:
            return self.articol_label
        if self.articol_nr:
            return f"Articolul {self.articol_nr}"
        return f"Articol #{self.ordine or self.id}"
    
    @property
    def has_labels(self) -> bool:
        """Check if article has LLM-generated labels."""
        return bool(self.issue or self.explicatie)
    
    @property
    def hierarchy_path(self) -> str:
        """Generate hierarchy path string."""
        parts = []
        if self.titlu_nr:
            parts.append(f"Titlul {self.titlu_nr}")
        if self.capitol_nr:
            parts.append(f"Cap. {self.capitol_nr}")
        if self.sectiune_nr:
            parts.append(f"Sect. {self.sectiune_nr}")
        if self.subsectiune_nr:
            parts.append(f"Subsect. {self.subsectiune_nr}")
        return " > ".join(parts) if parts else "N/A"

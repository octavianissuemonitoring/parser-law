"""
SQLAlchemy models for Issues Junction Tables.

Implements many-to-many relationships between documents and issues:
- Tier 1: Direct issues (ArticolIssue, ActIssue, AnexaIssue)
- Tier 2: Structural issues (StructureIssue for titlu/capitol/sectiune)

All issues are contextualized within a specific Domeniu (domain).
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.act_legislativ import ActLegislativ
    from app.models.articol import Articol
    from app.models.anexa import Anexa
    from app.models.issue import Issue
    from app.models.domeniu import Domeniu


class ArticolIssue(Base):
    """
    Junction table: Articol <-> Issue (many-to-many) - TIER 1.
    
    Links issues directly to specific articles.
    Issues are contextualized by domain - same article can have
    different issues for different domains.
    """
    
    __tablename__ = "articole_issues"
    __table_args__ = {"schema": "legislatie"}
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    articol_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.articole.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    issue_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    domeniu_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.domenii.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="MANDATORY: Issue context is always within a specific domain"
    )
    
    # Metadata
    relevance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        nullable=True,
        comment="AI-assigned relevance (0.00-1.00)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp()
    )
    
    # Relationships
    articol: Mapped["Articol"] = relationship(
        "Articol",
        back_populates="articole_issues"
    )
    issue: Mapped["Issue"] = relationship("Issue")
    domeniu: Mapped["Domeniu"] = relationship("Domeniu")
    
    def __repr__(self) -> str:
        return f"<ArticolIssue(articol_id={self.articol_id}, issue_id={self.issue_id}, domeniu_id={self.domeniu_id})>"


class ActIssue(Base):
    """
    Junction table: ActLegislativ <-> Issue (many-to-many) - TIER 1.
    
    Links issues to entire legislative acts (act-level themes).
    """
    
    __tablename__ = "acte_issues"
    __table_args__ = {"schema": "legislatie"}
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    act_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.acte_legislative.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    issue_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    domeniu_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.domenii.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Metadata
    relevance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp()
    )
    
    # Relationships
    act: Mapped["ActLegislativ"] = relationship(
        "ActLegislativ",
        back_populates="acte_issues"
    )
    issue: Mapped["Issue"] = relationship("Issue")
    domeniu: Mapped["Domeniu"] = relationship("Domeniu")
    
    def __repr__(self) -> str:
        return f"<ActIssue(act_id={self.act_id}, issue_id={self.issue_id}, domeniu_id={self.domeniu_id})>"


class AnexaIssue(Base):
    """
    Junction table: Anexa <-> Issue (many-to-many) - TIER 1.
    
    Links issues to annexes of legislative acts.
    """
    
    __tablename__ = "anexe_issues"
    __table_args__ = {"schema": "legislatie"}
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    anexa_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.anexe.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    issue_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    domeniu_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.domenii.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Metadata
    relevance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp()
    )
    
    # Relationships
    anexa: Mapped["Anexa"] = relationship(
        "Anexa",
        back_populates="anexe_issues"
    )
    issue: Mapped["Issue"] = relationship("Issue")
    domeniu: Mapped["Domeniu"] = relationship("Domeniu")
    
    def __repr__(self) -> str:
        return f"<AnexaIssue(anexa_id={self.anexa_id}, issue_id={self.issue_id}, domeniu_id={self.domeniu_id})>"


class StructureIssue(Base):
    """
    Junction table: Structural Elements <-> Issue (many-to-many) - TIER 2.
    
    Links issues to structural elements (titlu, capitol, sectiune) within an act.
    These are parent-level issues that apply to all child articles within
    the structure, displayed in the UI tree at the structure level.
    
    Uses text identifiers (titlu_nr, capitol_nr, sectiune_nr) to reference
    structure without creating separate structure tables.
    """
    
    __tablename__ = "structure_issues"
    __table_args__ = (
        CheckConstraint(
            "structure_type IN ('titlu', 'capitol', 'sectiune')",
            name="structure_issues_structure_type_check"
        ),
        CheckConstraint(
            "relevance_score >= 0.00 AND relevance_score <= 1.00",
            name="structure_issues_relevance_score_check"
        ),
        {"schema": "legislatie"}
    )
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    act_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.acte_legislative.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    issue_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    domeniu_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.domenii.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Structure Identification
    structure_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Type: 'titlu', 'capitol', or 'sectiune'"
    )
    
    # Structure Identifiers (matches existing articole columns)
    titlu_nr: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Title number (e.g., 'I', 'II', 'III-A') when structure_type='titlu'"
    )
    titlu_denumire: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional: full title name for context"
    )
    capitol_nr: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Chapter number (e.g., '1', '2', '3bis') when structure_type='capitol'"
    )
    capitol_denumire: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional: full chapter name for context"
    )
    sectiune_nr: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Section number (e.g., '1', '2', 'A') when structure_type='sectiune'"
    )
    sectiune_denumire: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional: full section name for context"
    )
    
    # Metadata
    relevance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        nullable=True,
        comment="AI-assigned relevance for this structural element and its children"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp()
    )
    
    # Relationships
    act: Mapped["ActLegislativ"] = relationship(
        "ActLegislativ",
        back_populates="structure_issues"
    )
    issue: Mapped["Issue"] = relationship("Issue")
    domeniu: Mapped["Domeniu"] = relationship("Domeniu")
    
    def __repr__(self) -> str:
        return f"<StructureIssue(act_id={self.act_id}, type='{self.structure_type}', issue_id={self.issue_id}, domeniu_id={self.domeniu_id})>"

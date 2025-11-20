"""
SQLAlchemy models for Domenii (Domain/Category System).

Domenii represents thematic categories for legislative acts:
- Acts are assigned to one or more domains (e.g., FARMA, TUTUN)
- Articles can optionally override parent act's domains
- Issues are always contextualized within a specific domain
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.act_legislativ import ActLegislativ
    from app.models.articol import Articol


class Domeniu(Base):
    """
    Model pentru domenii/categorii tematice de legislație.
    
    Examples: Produse Farmaceutice, Dispozitive Medicale, Tutun, etc.
    Used to organize and filter legislative acts by subject matter.
    """
    
    __tablename__ = "domenii"
    __table_args__ = {"schema": "legislatie"}
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identificare
    cod: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique code identifier (e.g., FARMA, TUTUN, DISP_MED)"
    )
    denumire: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name (e.g., Produse Farmaceutice)"
    )
    descriere: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the domain"
    )
    
    # UI Customization
    culoare: Mapped[Optional[str]] = mapped_column(
        String(7),
        nullable=True,
        comment="Hex color code for UI (e.g., #3B82F6)"
    )
    ordine: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order in lists/dropdowns (lower = first)"
    )
    
    # Status
    activ: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft delete flag - inactive domains hidden in UI"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        comment="Creation timestamp"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.current_timestamp(),
        comment="Last update timestamp"
    )
    
    # Relationships
    acte_domenii: Mapped[List["ActDomeniu"]] = relationship(
        "ActDomeniu",
        back_populates="domeniu",
        cascade="all, delete-orphan"
    )
    articole_domenii: Mapped[List["ArticolDomeniu"]] = relationship(
        "ArticolDomeniu",
        back_populates="domeniu",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Domeniu(id={self.id}, cod='{self.cod}', denumire='{self.denumire}')>"


class ActDomeniu(Base):
    """
    Junction table: ActLegislativ <-> Domeniu (many-to-many).
    
    Assigns domains to legislative acts when user imports/scrapes them.
    All articles inherit these domains unless overridden.
    """
    
    __tablename__ = "acte_domenii"
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
    domeniu_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.domenii.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Metadata
    relevanta: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        nullable=True,
        comment="Optional relevance score (0.00-1.00) - how relevant is this act to this domain"
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp()
    )
    added_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="User who assigned this domain (optional)"
    )
    
    # Relationships
    act: Mapped["ActLegislativ"] = relationship(
        "ActLegislativ",
        back_populates="acte_domenii"
    )
    domeniu: Mapped["Domeniu"] = relationship(
        "Domeniu",
        back_populates="acte_domenii"
    )
    
    def __repr__(self) -> str:
        return f"<ActDomeniu(act_id={self.act_id}, domeniu_id={self.domeniu_id})>"


class ArticolDomeniu(Base):
    """
    Junction table: Articol <-> Domeniu (many-to-many).
    
    OPTIONAL override - if set, article uses these domains instead of 
    inheriting from parent act. Used when specific articles apply to
    additional or different domains than the parent act.
    
    Example: Pharmaceutical act (FARMA) with one article also relevant to Tobacco (TUTUN).
    """
    
    __tablename__ = "articole_domenii"
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
    domeniu_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.domenii.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Metadata
    relevanta: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        nullable=True,
        comment="Optional relevance score (0.00-1.00)"
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp()
    )
    added_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="User who assigned this domain override"
    )
    
    # Relationships
    articol: Mapped["Articol"] = relationship(
        "Articol",
        back_populates="articole_domenii"
    )
    domeniu: Mapped["Domeniu"] = relationship(
        "Domeniu",
        back_populates="articole_domenii"
    )
    
    def __repr__(self) -> str:
        return f"<ArticolDomeniu(articol_id={self.articol_id}, domeniu_id={self.domeniu_id})>"

"""
SQLAlchemy model for Act Legislativ (Legislative Act).
"""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import String, Integer, Date, Text, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ActLegislativ(Base):
    """
    Model pentru actele legislative.
    
    Stochează metadata completă despre un act legislativ
    (LEGE, ORDONANȚĂ, METODOLOGIE, etc.).
    """
    
    __tablename__ = "acte_legislative"
    __table_args__ = {"schema": "legislatie"}
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identificare Act
    tip_act: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    nr_act: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    data_act: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    an_act: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    
    # Denumire
    titlu_act: Mapped[str] = mapped_column(Text, nullable=False)
    emitent_act: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Monitorul Oficial
    mof_nr: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mof_data: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    mof_an: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    
    # URL & Content
    url_legislatie: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Quality Metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), 
        nullable=True,
        comment="Parsing confidence score (0.00-1.00)"
    )
    
    # Versioning
    versiune: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="Version number (incremented on updates)"
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
    articole: Mapped[List["Articol"]] = relationship(
        "Articol",
        back_populates="act",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<ActLegislativ(id={self.id}, tip={self.tip_act}, nr={self.nr_act}, an={self.an_act})>"
    
    @property
    def display_name(self) -> str:
        """Generate display name for the act."""
        parts = [self.tip_act]
        if self.nr_act:
            parts.append(f"nr. {self.nr_act}")
        if self.an_act:
            parts.append(f"din {self.an_act}")
        return " ".join(parts)
    
    @property
    def articole_count(self) -> int:
        """Count of articole (requires articole to be loaded)."""
        return len(self.articole) if self.articole else 0

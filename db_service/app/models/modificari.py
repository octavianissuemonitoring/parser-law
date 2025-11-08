"""
SQLAlchemy models for article change tracking.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ActeModificari(Base):
    """
    Track modifications to legislative acts.
    Records when an act is updated and statistics about changes.
    """
    
    __tablename__ = "acte_modificari"
    __table_args__ = {"schema": "legislatie"}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    act_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.acte_legislative.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    versiune: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Modification metadata
    data_modificare: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    tip_modificare: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="initial, update_full, update_partial"
    )
    sursa_modificare: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    modificat_de: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Change statistics
    articole_noi: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    articole_modificate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    articole_sterse: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_articole: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    articole_modificari: Mapped[list["ArticoleModificari"]] = relationship(
        "ArticoleModificari",
        back_populates="modificare",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ActeModificari(id={self.id}, act_id={self.act_id}, versiune={self.versiune})>"


class ArticoleModificari(Base):
    """
    Track individual article changes for re-labeling purposes.
    
    Stores diff information to determine which articles need LLM re-processing:
    - added: New articles that need initial labeling
    - modified: Changed articles that need re-labeling
    - deleted: Removed articles (for cleanup)
    - unchanged: Articles that don't need re-processing
    """
    
    __tablename__ = "articole_modificari"
    __table_args__ = {"schema": "legislatie"}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    modificare_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("legislatie.acte_modificari.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    articol_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("legislatie.articole.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="NULL for deleted articles"
    )
    
    # Article identification
    articol_nr: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    articol_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ordine: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Change type
    tip_schimbare: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="added, modified, deleted, unchanged"
    )
    
    # Old values (for comparison and rollback)
    text_vechi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issue_vechi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explicatie_veche: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # New values
    text_nou: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Re-labeling tracking
    necesita_reetichetare: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reetichetat: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    reetichetat_la: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    modificare: Mapped["ActeModificari"] = relationship(
        "ActeModificari",
        back_populates="articole_modificari"
    )
    
    def __repr__(self) -> str:
        return f"<ArticoleModificari(id={self.id}, articol_nr={self.articol_nr}, tip={self.tip_schimbare})>"
    
    @property
    def display_name(self) -> str:
        """Generate display name for the article change."""
        if self.articol_label:
            return f"{self.articol_label} ({self.tip_schimbare})"
        if self.articol_nr:
            return f"Art. {self.articol_nr} ({self.tip_schimbare})"
        return f"Ordine {self.ordine} ({self.tip_schimbare})"
    
    @property
    def has_text_change(self) -> bool:
        """Check if text content changed."""
        if self.tip_schimbare in ['added', 'deleted']:
            return True
        return self.text_vechi != self.text_nou if self.text_vechi and self.text_nou else False
    
    def to_llm_payload(self) -> dict:
        """
        Generate payload for LLM re-labeling service.
        
        Returns dict with:
        - article_id
        - change_type
        - old_text, old_issue, old_explanation (if modified/deleted)
        - new_text (if added/modified)
        """
        payload = {
            "article_id": self.articol_id,
            "articol_nr": self.articol_nr,
            "change_type": self.tip_schimbare,
        }
        
        if self.tip_schimbare in ['modified', 'deleted']:
            payload["old"] = {
                "text": self.text_vechi,
                "issue": self.issue_vechi,
                "explicatie": self.explicatie_veche,
            }
        
        if self.tip_schimbare in ['added', 'modified']:
            payload["new"] = {
                "text": self.text_nou,
            }
        
        return payload

"""Link legislatie model for storing legislation URLs."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database import Base


class LinkStatus(str, enum.Enum):
    """Status enum for link processing."""
    PENDING = "pending_scraping"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LinkLegislatie(Base):
    """Model for storing legislation links."""
    
    __tablename__ = "linkuri_legislatie"
    __table_args__ = {"schema": "legislatie"}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=LinkStatus.PENDING,
        server_default=LinkStatus.PENDING
    )
    acte_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        onupdate=datetime.utcnow
    )
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<LinkLegislatie(id={self.id}, url={self.url[:50]}..., status={self.status})>"

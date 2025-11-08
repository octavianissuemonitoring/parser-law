"""
API Dependencies - Common dependencies for API routes.
"""
from typing import AsyncGenerator, Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db


# Database session dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async for session in get_db():
        yield session


# Type alias for database session dependency
DBSession = Annotated[AsyncSession, Depends(get_session)]


# Pagination dependencies
class PaginationParams:
    """Pagination parameters."""
    
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    ):
        self.skip = skip
        self.limit = limit


# Type alias for pagination dependency
Pagination = Annotated[PaginationParams, Depends()]

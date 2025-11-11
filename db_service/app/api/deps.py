"""
API Dependencies - Common dependencies for API routes.
"""
from typing import AsyncGenerator, Annotated

from fastapi import Depends, Query, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings


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


# Security dependencies
async def verify_api_key(
    x_api_key: str = Header(None, alias=settings.api_key_header)
) -> str:
    """
    Verify API key for protected endpoints.
    
    Raises:
        HTTPException: If API key is missing or invalid
        
    Returns:
        The validated API key
    """
    if not settings.api_key:
        # No API key configured - allow access (for development)
        return "development"
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing. Provide via X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return x_api_key


async def verify_ip_whitelist(request: Request) -> str:
    """
    Verify client IP is whitelisted (if whitelist is configured).
    
    Raises:
        HTTPException: If IP is not whitelisted
        
    Returns:
        The client IP address
    """
    if not settings.allowed_ips:
        # No whitelist configured - allow all IPs
        return request.client.host
    
    client_ip = request.client.host
    
    if client_ip not in settings.allowed_ips:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied for IP: {client_ip}"
        )
    
    return client_ip


# Combined security check
async def require_auth(
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(verify_ip_whitelist)
) -> dict:
    """
    Combined authentication check (API key + IP whitelist).
    
    Use this dependency for protected endpoints.
    """
    return {
        "api_key": api_key,
        "client_ip": client_ip
    }


# Type aliases for dependencies
APIKey = Annotated[str, Depends(verify_api_key)]
ClientIP = Annotated[str, Depends(verify_ip_whitelist)]
AuthInfo = Annotated[dict, Depends(require_auth)]


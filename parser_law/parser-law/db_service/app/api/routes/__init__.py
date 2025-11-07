"""
API Routes package.
"""
from app.api.routes.acte import router as acte_router
from app.api.routes.articole import router as articole_router

__all__ = ["acte_router", "articole_router"]

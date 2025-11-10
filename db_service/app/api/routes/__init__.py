"""
API Routes package.
"""
from app.api.routes.acte import router as acte_router
from app.api.routes.articole import router as articole_router
from app.api.routes.stats import router as stats_router
from app.api.routes.issues import router as issues_router
from app.api.routes.categories import router as categories_router

__all__ = ["acte_router", "articole_router", "stats_router", "issues_router", "categories_router"]

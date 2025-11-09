"""
FastAPI main application.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    """
    # Startup
    print("🚀 Starting API...")
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down API...")
    await close_db()
    print("✅ Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.api_title,
        "version": settings.api_version,
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API info."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "web_ui": "/static/index.html",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "acte": "/api/v1/acte",
            "articole": "/api/v1/articole",
            "ai_processing": "/api/v1/ai",
            "export": "/api/v1/export",
            "links": "/api/v1/links",
        },
    }


# Import and include routers
from app.api.routes import acte_router, articole_router
from app.api.routes.ai_processing import router as ai_router
from app.api.routes.export import router as export_router
from app.api.routes.links import router as links_router

app.include_router(acte_router, prefix="/api/v1")
app.include_router(articole_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(links_router, prefix="/api/v1")

# Mount static files (must be last to not override API routes)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )

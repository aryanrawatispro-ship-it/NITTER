"""
FastAPI main application - Community Scraper Only.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from src.utils.config import settings
from src.api.routes import communities, export

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>"
)
logger.add(
    settings.log_file,
    rotation="500 MB",
    retention="10 days",
    level=settings.log_level
)

# Create FastAPI app
app = FastAPI(
    title="Twitter Community Scraper API",
    description="API for scraping Twitter Community tweets using TwitterAPI.io or Twitter Direct",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - ONLY communities and export!
app.include_router(communities.router, prefix="/api/communities", tags=["Communities"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Twitter Community Scraper API",
        "version": "2.0.0",
        "description": "Scrape tweets from Twitter Communities",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Starting Twitter Community Scraper API...")
    logger.info(f"API running on {settings.api_host}:{settings.api_port}")
    logger.info("Endpoints: /api/communities, /api/export")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down Twitter Community Scraper API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

"""
FastAPI main application.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from src.utils.config import settings
from src.api.routes import users, tweets, search, jobs, webhooks, export, dashboard

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
    title="Nitter Twitter Scraper API",
    description="API for scraping and analyzing Twitter data using Nitter instances",
    version="1.0.0",
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

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(tweets.router, prefix="/api/tweets", tags=["Tweets"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Nitter Twitter Scraper API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Starting Nitter Scraper API...")
    logger.info(f"API running on {settings.api_host}:{settings.api_port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down Nitter Scraper API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

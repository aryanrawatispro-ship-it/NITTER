"""
Scraping job monitoring API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from pydantic import BaseModel
from datetime import datetime

from src.utils.database import get_db
from src.utils.models import ScrapingJob

router = APIRouter()


class JobResponse(BaseModel):
    id: int
    job_id: str
    job_type: str
    target: str
    status: str
    items_scraped: int
    error_message: str = None
    created_at: datetime
    started_at: datetime = None
    completed_at: datetime = None
    duration: float = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[JobResponse])
async def get_jobs(
    status: str = None,
    job_type: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get scraping jobs with optional filters.

    Filters:
    - status: Filter by status (pending, running, completed, failed)
    - job_type: Filter by type (profile, timeline, search, thread)
    """
    query = db.query(ScrapingJob)

    if status:
        query = query.filter_by(status=status)

    if job_type:
        query = query.filter_by(job_type=job_type)

    jobs = query.order_by(desc(ScrapingJob.created_at)).offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get details of a specific job."""
    job = db.query(ScrapingJob).filter_by(job_id=job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.get("/stats/summary")
async def get_job_stats(db: Session = Depends(get_db)):
    """Get summary statistics for scraping jobs."""
    from sqlalchemy import func

    total_jobs = db.query(func.count(ScrapingJob.id)).scalar()
    completed = db.query(func.count(ScrapingJob.id)).filter_by(status='completed').scalar()
    failed = db.query(func.count(ScrapingJob.id)).filter_by(status='failed').scalar()
    running = db.query(func.count(ScrapingJob.id)).filter_by(status='running').scalar()
    pending = db.query(func.count(ScrapingJob.id)).filter_by(status='pending').scalar()

    total_items = db.query(func.sum(ScrapingJob.items_scraped)).scalar() or 0
    avg_duration = db.query(func.avg(ScrapingJob.duration)).filter(
        ScrapingJob.status == 'completed'
    ).scalar() or 0

    return {
        "total_jobs": total_jobs,
        "completed": completed,
        "failed": failed,
        "running": running,
        "pending": pending,
        "total_items_scraped": total_items,
        "avg_duration_seconds": round(avg_duration, 2),
        "success_rate": round((completed / total_jobs * 100), 2) if total_jobs > 0 else 0
    }

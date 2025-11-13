"""
Search API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from src.utils.database import get_db
from src.utils.models import SearchQuery
from src.scheduler.tasks import scrape_search_results, schedule_search_tracking

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    search_type: str = "keyword"
    track: bool = False
    check_interval: int = 3600


class SearchResponse(BaseModel):
    id: int
    query: str
    query_type: str
    is_active: bool
    total_results: int
    last_executed: str

    class Config:
        from_attributes = True


@router.post("/", status_code=201)
async def create_search(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Create a new search and optionally track it.

    Args:
        query: Search query
        search_type: Type (keyword, hashtag, user)
        track: Whether to track this search periodically
        check_interval: Interval for tracking (seconds)
    """
    # Trigger immediate search
    scrape_search_results.delay(request.query, request.search_type, max_tweets=100)

    if request.track:
        schedule_search_tracking(request.query, request.search_type, request.check_interval)

    return {
        "message": f"Search created for '{request.query}'",
        "query": request.query,
        "tracked": request.track
    }


@router.get("/tracked", response_model=List[SearchResponse])
async def get_tracked_searches(db: Session = Depends(get_db)):
    """Get all tracked search queries."""
    searches = db.query(SearchQuery).filter_by(is_active=True).all()

    result = []
    for search in searches:
        result.append({
            "id": search.id,
            "query": search.query,
            "query_type": search.query_type,
            "is_active": search.is_active,
            "total_results": search.total_results,
            "last_executed": search.last_executed.isoformat() if search.last_executed else "Never"
        })

    return result


@router.delete("/{search_id}")
async def delete_search(search_id: int, db: Session = Depends(get_db)):
    """Deactivate a tracked search."""
    search = db.query(SearchQuery).filter_by(id=search_id).first()

    if not search:
        raise HTTPException(status_code=404, detail="Search not found")

    search.is_active = False
    db.commit()

    return {"message": "Search deactivated"}


@router.post("/{search_id}/execute")
async def execute_search(search_id: int, db: Session = Depends(get_db)):
    """Manually execute a search."""
    search = db.query(SearchQuery).filter_by(id=search_id).first()

    if not search:
        raise HTTPException(status_code=404, detail="Search not found")

    scrape_search_results.delay(search.query, search.query_type)

    return {"message": f"Executing search for '{search.query}'"}

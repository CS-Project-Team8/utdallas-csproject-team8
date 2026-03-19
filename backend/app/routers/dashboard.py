from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import StudioDashboardOut, MovieCardOut
from app.services.dashboard_service import (
    get_studio_dashboard,
    get_dashboard_movies,
    search_studio_movies,
)

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/studios/{studio_id}", response_model=StudioDashboardOut)
def read_studio_dashboard(studio_id: str, db: Session = Depends(get_db)):
    data = get_studio_dashboard(db, studio_id)
    if not data:
        raise HTTPException(status_code=404, detail="Studio not found")
    return data


@router.get("/studios/{studio_id}/movies", response_model=List[MovieCardOut])
def read_dashboard_movies(studio_id: str, db: Session = Depends(get_db)):
    return get_dashboard_movies(db, studio_id)

@router.get("/studios/{studio_id}/movies/search", response_model=List[MovieCardOut])
def read_search_movies(
        studio_id: str,
        query: str = Query(default=""),
        limit: int = Query(default=12, ge=1, le=50),
        db: Session = Depends(get_db),
):
    return search_studio_movies(db, studio_id, query, limit)
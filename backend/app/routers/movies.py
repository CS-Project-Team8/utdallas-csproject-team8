from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.session import engine

router = APIRouter(prefix="/api/v1", tags=["movies"])


@router.get("/studios/{studio_id}/movies/{movie_id}")
def get_movie(studio_id: UUID, movie_id: UUID):
    query = text("""
        SELECT
            movieid,
            studioid,
            title,
            rating,
            "posterUrl" AS posterurl
        FROM movies
        WHERE studioid = :studio_id
          AND movieid = :movie_id
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(
            query,
            {
                "studio_id": studio_id,
                "movie_id": movie_id,
            },
        ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Movie not found")

    return {
        "movieid": str(row["movieid"]),
        "studioid": str(row["studioid"]),
        "title": row["title"],
        "year": None,
        "posterUrl": row["posterurl"],
        "rating": row["rating"],
    }
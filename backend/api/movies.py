"""
Movies API Endpoints
--------------------
Handles movie retrieval, pagination, title search, single-movie lookup,
and similar movie inspection.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status
from backend.services.data_service import data_service
from backend.models.schemas import Movie, MovieListResponse, SearchResponse

router = APIRouter(prefix="/api/movies", tags=["Movies"])


@router.get(
    "",
    response_model=MovieListResponse,
    summary="Get Paginated Movies",
    description="Retrieve paginated movie records with optional genre filtering and dynamic sorting."
)
def get_movies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    genre: Optional[str] = Query(None, description="Filter by genre name (e.g., Action)"),
    sort_by: str = Query("popularity", description="Sort by: popularity, rating, votes, title, year")
):
    movies, total, latency_ms = data_service.get_movies(
        page=page,
        page_size=page_size,
        genre=genre,
        sort_by=sort_by
    )
    return MovieListResponse(
        total=total,
        page=page,
        page_size=page_size,
        results=movies,
        execution_time_ms=latency_ms
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search Movies by Title",
    description="Perform case-insensitive title search with relevance and popularity ranking."
)
def search_movies(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(20, ge=1, le=50, description="Maximum matches to return")
):
    clean_q = q.strip()
    if not clean_q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty or only whitespace."
        )

    matches, latency_ms = data_service.search_movies(query=clean_q, limit=limit)
    return SearchResponse(
        query=clean_q,
        count=len(matches),
        results=matches,
        execution_time_ms=latency_ms
    )


@router.get(
    "/{movie_id}",
    response_model=Movie,
    summary="Get Movie Details",
    description="Fetch full details and aggregated rating metadata for a specific movie ID."
)
def get_movie_details(movie_id: int):
    movie, _ = data_service.get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} was not found in the serving database."
        )
    return movie


@router.get(
    "/{movie_id}/similar",
    summary="Inspect Content Similarity Breakdown",
    description="Detailed inspection endpoint for academic demonstration showing TF-IDF similarity metrics."
)
def get_similar_breakdown(movie_id: int, limit: int = Query(5, ge=1, le=20)):
    movie, _ = data_service.get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} was not found."
        )

    from backend.services.recommendation_service import recommendation_service
    rec_res = recommendation_service.get_recommendations(movie_id=movie_id, top_k=limit)

    return {
        "movie_id": movie.movie_id,
        "title": movie.title,
        "genres": movie.genres,
        "similarity_method": "TF-IDF N-Gram Vectorization + Cosine Similarity",
        "serving_storage": "DuckDB Precomputed Serving Table ('recommendations')",
        "similar_movies": [
            {
                "rank": item.rank,
                "recommended_movie_id": item.movie_id,
                "title": item.title,
                "genres": item.genres,
                "similarity_score": item.similarity_score,
                "avg_rating": item.avg_rating
            }
            for item in rec_res.results
        ],
        "latency_ms": rec_res.processing_time_ms
    }

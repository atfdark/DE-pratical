"""
Analytics & Statistics API Endpoints
------------------------------------
Exposes analytical aggregations directly computed from the DuckDB serving store.
"""

from typing import List
from fastapi import APIRouter, Query, HTTPException, status
from backend.services.data_service import data_service
from backend.models.schemas import (
    DatasetStatsResponse,
    PopularResponse
)

router = APIRouter(prefix="/api", tags=["Analytics & Statistics"])


@router.get(
    "/stats",
    response_model=DatasetStatsResponse,
    summary="Get Dataset Analytics & Metrics",
    description="Returns aggregate statistics, genre distributions, rating histogram, and leaderboards."
)
def get_dataset_stats():
    try:
        return data_service.get_dataset_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dataset statistics: {e}"
        )


@router.get(
    "/popular",
    response_model=PopularResponse,
    summary="Get Popular Movies Leaderboard",
    description="Returns precomputed popular movies ranked by Bayesian weighted rating score."
)
def get_popular_movies(
    limit: int = Query(20, ge=1, le=50, description="Number of popular movies to return")
):
    try:
        items, latency_ms = data_service.get_popular_movies(limit=limit)
        return PopularResponse(
            count=len(items),
            results=items,
            execution_time_ms=latency_ms
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch popular movies: {e}"
        )


@router.get(
    "/genres",
    response_model=List[str],
    summary="Get Available Movie Genres",
    description="Returns list of all distinct genres present in the dataset."
)
def get_genres():
    try:
        return data_service.get_all_genres()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch genres: {e}"
        )

"""
Recommendations API Endpoints
-----------------------------
The core Data Serving recommendation endpoints.
Queries precomputed similarity rankings with Bayesian popularity fallback.
"""

from fastapi import APIRouter, Query, HTTPException, status
from backend.services.recommendation_service import recommendation_service
from backend.services.data_service import data_service
from backend.models.schemas import RecommendationResponse, RecommendRequest

router = APIRouter(tags=["Recommendations"])


@router.get(
    "/api/movies/{movie_id}/recommendations",
    response_model=RecommendationResponse,
    summary="Get Movie Recommendations",
    description="Returns precomputed Top-K content recommendations from DuckDB with sub-millisecond serving latency."
)
def get_recommendations_for_movie(
    movie_id: int,
    top_k: int = Query(10, ge=1, le=50, description="Number of recommendations to retrieve")
):
    try:
        response = recommendation_service.get_recommendations(movie_id=movie_id, top_k=top_k)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying recommendation serving store: {e}"
        )


@router.post(
    "/api/recommend",
    response_model=RecommendationResponse,
    summary="Query Recommendations via JSON Payload",
    description="Accepts either movie_id or movie title string to deliver recommendations."
)
def post_recommend(payload: RecommendRequest):
    target_movie_id = payload.movie_id

    # If title provided instead of movie_id, search for best title match
    if not target_movie_id:
        if not payload.title or not payload.title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'movie_id' or 'title' must be supplied."
            )
        matches, _ = data_service.search_movies(payload.title.strip(), limit=1)
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No movie found matching title '{payload.title}'."
            )
        target_movie_id = matches[0].movie_id

    try:
        return recommendation_service.get_recommendations(
            movie_id=target_movie_id,
            top_k=payload.top_k
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal serving error: {e}"
        )

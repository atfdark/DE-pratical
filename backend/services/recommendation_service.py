"""
Recommendation Service: Serving Layer Recommendation Delivery
--------------------------------------------------------------
Queries precomputed content-based recommendations directly from DuckDB serving tables.
Features:
- Sub-millisecond serving from precomputed DuckDB tables
- Dynamic fallback to Bayesian popular movies when metadata similarity is sparse
- Transparent explanation of similarity scores and fallback rationale
- Exact wall-clock latency measurement
"""

import time
import logging
from typing import Tuple, Optional, List

from backend.db.duckdb_client import db_client
from backend.services.data_service import data_service
from backend.models.schemas import (
    Movie,
    RecommendationItem,
    RecommendationResponse
)

logger = logging.getLogger("backend.recommendation_service")


class RecommendationService:
    """Delivers precomputed recommendations from DuckDB with intelligent fallback."""

    def __init__(self):
        self.db = db_client
        self.data_service = data_service

    def get_recommendations(
        self,
        movie_id: int,
        top_k: int = 10
    ) -> RecommendationResponse:
        """
        Serve Top-K recommendations for a target movie.
        Queries DuckDB 'recommendations' table joined with 'movies' and 'ratings_summary'.
        Applies fallback if recommendations are unavailable or insufficient.
        """
        start_time = time.perf_counter()

        # 1. Fetch source movie details
        source_movie, _ = self.data_service.get_movie_by_id(movie_id)
        if not source_movie:
            raise ValueError(f"Movie with ID {movie_id} does not exist.")

        # 2. Query precomputed recommendations from DuckDB
        rec_sql = """
            SELECT
                r.rank,
                m.movie_id,
                m.title,
                m.genres,
                m.release_year,
                COALESCE(s.avg_rating, 0.0) as avg_rating,
                COALESCE(s.rating_count, 0) as rating_count,
                COALESCE(s.popularity_score, 0.0) as popularity_score,
                r.similarity_score
            FROM recommendations r
            JOIN movies m ON r.recommended_movie_id = m.movie_id
            LEFT JOIN ratings_summary s ON m.movie_id = s.movie_id
            WHERE r.movie_id = ?
            ORDER BY r.rank ASC
            LIMIT ?;
        """
        rows, query_latency_ms = self.db.query(rec_sql, [movie_id, top_k])

        is_fallback = False
        fallback_reason = None
        results: List[RecommendationItem] = []

        # 3. Check if recommendations exist and are adequate
        if rows and len(rows) > 0:
            for row in rows:
                results.append(RecommendationItem(**row))
        else:
            # Fallback triggered: retrieve top popular movies excluding source movie
            is_fallback = True
            fallback_reason = (
                "Insufficient content similarity metadata for this movie. "
                "Serving top Bayesian popular movies as high-confidence fallback."
            )
            logger.info(f"Fallback activated for movie_id={movie_id}: {fallback_reason}")

            fallback_sql = """
                SELECT
                    p.rank,
                    m.movie_id,
                    m.title,
                    m.genres,
                    m.release_year,
                    s.avg_rating,
                    s.rating_count,
                    p.popularity_score,
                    0.0 as similarity_score
                FROM popular_movies p
                JOIN movies m ON p.movie_id = m.movie_id
                JOIN ratings_summary s ON m.movie_id = s.movie_id
                WHERE m.movie_id != ?
                ORDER BY p.rank ASC
                LIMIT ?;
            """
            fallback_rows, _ = self.db.query(fallback_sql, [movie_id, top_k])
            for rank_idx, row in enumerate(fallback_rows, start=1):
                row["rank"] = rank_idx
                results.append(RecommendationItem(**row))

        total_latency_ms = (time.perf_counter() - start_time) * 1000

        return RecommendationResponse(
            source_movie=source_movie,
            count=len(results),
            is_fallback=is_fallback,
            fallback_reason=fallback_reason,
            results=results,
            processing_time_ms=round(total_latency_ms, 3)
        )


recommendation_service = RecommendationService()

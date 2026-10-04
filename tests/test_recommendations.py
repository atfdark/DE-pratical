"""
Recommendation Engine & Serving Logic Tests
--------------------------------------------
Validates TF-IDF similarity characteristics, ranking order, score ranges,
exclusion of self-recommendations, and Bayesian fallback behavior.
"""

import pytest
from backend.services.recommendation_service import recommendation_service
from backend.services.data_service import data_service


def test_recommendation_for_star_wars():
    # Star Wars (movie_id = 50)
    response = recommendation_service.get_recommendations(movie_id=50, top_k=5)
    assert response.source_movie.movie_id == 50
    assert "Star Wars" in response.source_movie.title
    assert response.count == 5
    assert not response.is_fallback
    assert response.processing_time_ms >= 0.0

    # Ensure recommendations are strictly sorted by rank
    ranks = [r.rank for r in response.results]
    assert ranks == [1, 2, 3, 4, 5]

    # Check similarity score validity
    for rec in response.results:
        assert 0.0 <= rec.similarity_score <= 1.0
        assert rec.movie_id != 50  # No self-recommendations
        assert rec.title is not None
        assert rec.avg_rating > 0.0


def test_recommendation_for_toy_story():
    # Toy Story (movie_id = 1)
    response = recommendation_service.get_recommendations(movie_id=1, top_k=10)
    assert response.source_movie.movie_id == 1
    assert "Toy Story" in response.source_movie.title
    assert response.count == 10
    # Scores should be non-increasing with rank
    scores = [r.similarity_score for r in response.results]
    assert scores == sorted(scores, reverse=True)


def test_recommendation_nonexistent_movie_raises_error():
    with pytest.raises(ValueError):
        recommendation_service.get_recommendations(movie_id=999999, top_k=5)


def test_popular_movies_leaderboard():
    items, latency_ms = data_service.get_popular_movies(limit=10)
    assert len(items) == 10
    assert latency_ms >= 0.0

    # Ranks should be 1 to 10
    for idx, item in enumerate(items, start=1):
        assert item.rank == idx
        assert item.popularity_score > 0.0
        assert item.rating_count > 0


def test_serving_latency_is_low():
    # Data serving layer should execute recommendation query quickly (< 100ms)
    response = recommendation_service.get_recommendations(movie_id=1, top_k=5)
    assert response.processing_time_ms < 100.0, f"Serving too slow: {response.processing_time_ms} ms"

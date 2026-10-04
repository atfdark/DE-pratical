"""
API Integration Tests
---------------------
Tests all FastAPI REST endpoints, response codes, JSON payloads,
and error handling conditions.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root_health_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["movies_count"] >= 1682
    assert data["recommendations_count"] >= 20000
    assert "timestamp" in data


def test_get_movies_paginated():
    res = client.get("/api/movies?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["results"]) == 10
    assert data["total"] >= 1682
    assert "execution_time_ms" in data


def test_get_movies_genre_filter():
    res = client.get("/api/movies?genre=Animation&page_size=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) > 0
    for movie in data["results"]:
        assert "Animation" in movie["genres"]


def test_search_movies_found():
    res = client.get("/api/movies/search?q=Toy")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    assert any("Toy Story" in m["title"] for m in data["results"])


def test_search_movies_empty_query():
    res = client.get("/api/movies/search?q=   ")
    assert res.status_code == 400


def test_search_movies_no_results():
    res = client.get("/api/movies/search?q=Supercalifragilistic12345NonExistent")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 0
    assert data["results"] == []


def test_get_movie_details_valid():
    res = client.get("/api/movies/1")
    assert res.status_code == 200
    data = res.json()
    assert data["movie_id"] == 1
    assert "Toy Story" in data["title"]
    assert data["rating_count"] > 0


def test_get_movie_details_not_found():
    res = client.get("/api/movies/999999")
    assert res.status_code == 404


def test_get_recommendations_endpoint():
    res = client.get("/api/movies/1/recommendations?top_k=5")
    assert res.status_code == 200
    data = res.json()
    assert data["source_movie"]["movie_id"] == 1
    assert data["count"] == 5
    assert len(data["results"]) == 5
    assert data["processing_time_ms"] > 0.0


def test_get_recommendations_not_found():
    res = client.get("/api/movies/999999/recommendations")
    assert res.status_code == 404


def test_get_popular_endpoint():
    res = client.get("/api/popular?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 10
    assert len(data["results"]) == 10


def test_get_stats_endpoint():
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_movies"] >= 1682
    assert data["total_ratings"] >= 100000
    assert data["average_rating"] > 0.0
    assert len(data["genres"]) >= 18
    assert len(data["rating_distribution"]) >= 5


def test_get_genres_endpoint():
    res = client.get("/api/genres")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert "Action" in data
    assert "Comedy" in data


def test_post_recommend_by_id():
    res = client.post("/api/recommend", json={"movie_id": 50, "top_k": 5})
    assert res.status_code == 200
    data = res.json()
    assert data["source_movie"]["movie_id"] == 50
    assert data["count"] == 5


def test_post_recommend_by_title():
    res = client.post("/api/recommend", json={"title": "Star Wars", "top_k": 5})
    assert res.status_code == 200
    data = res.json()
    assert "Star Wars" in data["source_movie"]["title"]
    assert data["count"] == 5


def test_post_recommend_invalid():
    res = client.post("/api/recommend", json={})
    assert res.status_code == 400

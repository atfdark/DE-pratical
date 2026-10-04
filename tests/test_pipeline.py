"""
Pipeline Unit & Integration Tests
---------------------------------
Verifies data ingestion, schema validity, cleaning, feature transformation,
and DuckDB serving table builds.
"""

from pathlib import Path
import pytest
import pandas as pd
import duckdb

from backend.config import settings
from pipeline.ingest import load_genres, load_raw_movies, load_raw_ratings, validate_raw_data
from pipeline.clean import extract_year, clean_title, compile_genres, clean_movies, clean_ratings
from pipeline.transform import calculate_ratings_summary, create_feature_text

RAW_DIR = settings.RAW_DATA_DIR


@pytest.fixture(scope="module")
def raw_data():
    """Ensure raw dataset exists for testing."""
    if not (RAW_DIR / "u.item").exists():
        pytest.skip("MovieLens raw dataset not downloaded yet.")
    genre_map = load_genres(RAW_DIR)
    movies = load_raw_movies(RAW_DIR, genre_map)
    ratings = load_raw_ratings(RAW_DIR)
    return genre_map, movies, ratings


def test_genre_loading(raw_data):
    genre_map, _, _ = raw_data
    assert len(genre_map) >= 18
    assert 1 in genre_map  # Action
    assert "Action" in genre_map.values()


def test_raw_movies_schema(raw_data):
    _, movies, _ = raw_data
    assert len(movies) >= 1682
    expected_cols = ["movie_id", "title", "release_date"]
    for col in expected_cols:
        assert col in movies.columns
    assert movies["movie_id"].is_unique


def test_raw_ratings_schema(raw_data):
    _, _, ratings = raw_data
    assert len(ratings) >= 100000
    expected_cols = ["user_id", "movie_id", "rating", "timestamp"]
    for col in expected_cols:
        assert col in ratings.columns
    # Rating range validation
    assert ratings["rating"].between(1, 5).all()


def test_year_extraction():
    assert extract_year("Toy Story (1995)", None) == 1995
    assert extract_year("GoldenEye (1995)", "01-Jan-1995") == 1995
    assert extract_year("Star Wars (1977)", "") == 1977
    assert extract_year("Untitled", "15-Aug-1980") == 1980
    assert extract_year("No Year Here", None) == 0


def test_title_cleaning():
    assert clean_title("  Toy Story (1995)  ") == "Toy Story (1995)"
    assert clean_title("") == ""
    assert clean_title(None) == "Untitled"


def test_compile_genres():
    genre_cols = ["Action", "Sci-Fi", "Comedy", "unknown"]
    row_match = pd.Series({"Action": 1, "Sci-Fi": 1, "Comedy": 0, "unknown": 0})
    compiled = compile_genres(row_match, genre_cols)
    assert compiled == "Action|Sci-Fi"

    row_empty = pd.Series({"Action": 0, "Sci-Fi": 0, "Comedy": 0, "unknown": 1})
    assert compile_genres(row_empty, genre_cols) == "Unknown"


def test_ratings_summary_bayesian_logic():
    # Synthetic test ratings
    df = pd.DataFrame([
        {"user_id": 1, "movie_id": 1, "rating": 5},
        {"user_id": 2, "movie_id": 1, "rating": 5},
        {"user_id": 3, "movie_id": 2, "rating": 5},  # only 1 vote
        {"user_id": 4, "movie_id": 3, "rating": 1},
        {"user_id": 5, "movie_id": 3, "rating": 1},
    ])
    summary = calculate_ratings_summary(df, m_threshold=5)
    # Movie 1 has 2 votes of 5, Movie 2 has 1 vote of 5
    # Bayesian shrinkage should rank movie 1 higher popularity than movie 2
    row1 = summary[summary["movie_id"] == 1].iloc[0]
    row2 = summary[summary["movie_id"] == 2].iloc[0]
    assert row1["popularity_score"] > row2["popularity_score"]


def test_duckdb_serving_database_integrity():
    """Verify DuckDB serving database file exists and contains expected tables and rows."""
    db_path = settings.DB_PATH
    assert db_path.exists(), f"DuckDB file missing: {db_path}"

    con = duckdb.connect(str(db_path), read_only=True)
    tables = [r[0] for r in con.execute("SHOW TABLES;").fetchall()]
    expected_tables = ["movies", "ratings_summary", "recommendations", "popular_movies"]
    for t in expected_tables:
        assert t in tables, f"Table {t} missing from DuckDB serving database"

    movie_count = con.execute("SELECT COUNT(*) FROM movies;").fetchone()[0]
    rec_count = con.execute("SELECT COUNT(*) FROM recommendations;").fetchone()[0]
    con.close()

    assert movie_count >= 1682
    assert rec_count >= 20000

"""
Pipeline Step 1: Data Ingestion & Validation
---------------------------------------------
Loads raw MovieLens ml-latest-small files (movies, ratings),
validates schema integrity, data types, value ranges, and returns structured DataFrames.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Tuple, Any
import pandas as pd

logger = logging.getLogger("pipeline.ingest")

def load_raw_movies(raw_dir: Path) -> pd.DataFrame:
    item_path = raw_dir / "movies.csv"
    if not item_path.exists():
        raise FileNotFoundError(f"Missing required movie metadata file: {item_path}")

    df = pd.read_csv(item_path, dtype={"movieId": int})
    df = df.rename(columns={"movieId": "movie_id"})
    return df

def load_raw_ratings(raw_dir: Path) -> pd.DataFrame:
    data_path = raw_dir / "ratings.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Missing required ratings file: {data_path}")

    df = pd.read_csv(data_path, dtype={"userId": int, "movieId": int, "rating": float, "timestamp": int})
    df = df.rename(columns={"userId": "user_id", "movieId": "movie_id"})
    return df

def load_raw_users(raw_dir: Path) -> pd.DataFrame:
    return pd.DataFrame()

def validate_raw_data(
    movies_df: pd.DataFrame,
    ratings_df: pd.DataFrame
) -> Dict[str, Any]:
    logger.info("Validating raw datasets...")

    movie_count = len(movies_df)
    rating_count = len(ratings_df)
    logger.info(f"Loaded {movie_count} raw movies")
    logger.info(f"Loaded {rating_count} raw ratings")

    dup_movies = movies_df["movie_id"].duplicated().sum()
    dup_ratings = ratings_df.duplicated(subset=["user_id", "movie_id"]).sum()

    if dup_movies > 0:
        logger.warning(f"Found {dup_movies} duplicate movie IDs in movies.csv")
    if dup_ratings > 0:
        logger.warning(f"Found {dup_ratings} duplicate (user_id, movie_id) entries in ratings.csv")

    invalid_ratings = ratings_df[~ratings_df["rating"].between(0.5, 5.0)]
    invalid_rating_count = len(invalid_ratings)
    if invalid_rating_count > 0:
        logger.warning(f"Found {invalid_rating_count} ratings outside range [0.5, 5]")

    valid_movie_ids = set(movies_df["movie_id"])
    orphan_ratings = ratings_df[~ratings_df["movie_id"].isin(valid_movie_ids)]
    orphan_count = len(orphan_ratings)
    if orphan_count > 0:
        logger.warning(f"Found {orphan_count} ratings referencing nonexistent movie IDs")

    metrics = {
        "raw_movie_count": movie_count,
        "raw_rating_count": rating_count,
        "duplicate_movies": int(dup_movies),
        "duplicate_ratings": int(dup_ratings),
        "invalid_ratings": int(invalid_rating_count),
        "orphan_ratings": int(orphan_count)
    }
    return metrics

def run_ingestion(raw_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    logger.info("=" * 60)
    logger.info("PIPELINE STEP 1: INGESTION & DATA VALIDATION")
    logger.info("=" * 60)

    movies_df = load_raw_movies(raw_dir)
    ratings_df = load_raw_ratings(raw_dir)
    users_df = load_raw_users(raw_dir)

    metrics = validate_raw_data(movies_df, ratings_df)
    metrics["user_count"] = len(users_df) if not users_df.empty else 0

    logger.info(f"[INGESTION COMPLETE] {metrics['raw_movie_count']} movies, {metrics['raw_rating_count']} ratings")
    return movies_df, ratings_df, users_df, metrics

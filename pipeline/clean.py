"""
Pipeline Step 2: Data Cleaning & Normalization
----------------------------------------------
Cleans raw movies and ratings data:
- Deduplication
- Title and release year normalization
- Boundary validation on ratings (0.5-5 range)
- Removal of orphaned ratings
"""

import re
import logging
from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger("pipeline.clean")

def extract_year(title: str) -> int:
    """Extract 4-digit release year from movie title string."""
    if isinstance(title, str):
        match = re.search(r"\((\d{4})\)", title)
        if match:
            return int(match.group(1))
    return 0

def clean_title(title: str) -> str:
    """Normalize title by removing trailing whitespace and extra spaces."""
    if not isinstance(title, str):
        return "Untitled"
    # Clean whitespace
    cleaned = title.strip()
    return cleaned

def clean_movies(raw_movies: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean movies dataset and transform genre flags into standard column."""
    logger.info("Cleaning movies dataset...")
    initial_count = len(raw_movies)

    # Deduplicate by movie_id
    df = raw_movies.drop_duplicates(subset=["movie_id"]).copy()
    
    # Clean title first before deduplicating by title
    df["title"] = df["title"].apply(clean_title)
    
    # Deduplicate by title to remove API pagination dupes
    df = df.drop_duplicates(subset=["title"]).copy()
    
    dedup_count = initial_count - len(df)

    # Extract release year
    df["release_year"] = df.apply(
        lambda r: extract_year(r["title"]), axis=1
    )

    # Retain core columns
    clean_cols = ["movie_id", "title", "release_year", "genres"]
    clean_df = df[clean_cols].copy()

    metrics = {
        "movies_initial": initial_count,
        "movies_cleaned": len(clean_df),
        "movies_deduplicated": dedup_count
    }
    return clean_df, metrics

def clean_ratings(raw_ratings: pd.DataFrame, valid_movie_ids: set) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean ratings dataset and ensure referential integrity."""
    logger.info("Cleaning ratings dataset...")
    initial_count = len(raw_ratings)

    # Deduplicate user-movie pairs
    df = raw_ratings.drop_duplicates(subset=["user_id", "movie_id"]).copy()
    dedup_count = initial_count - len(df)

    # Filter invalid ratings (bounds check 0.5 to 5)
    valid_bounds = df["rating"].between(0.5, 5.0)
    df = df[valid_bounds]
    invalid_ratings_dropped = initial_count - dedup_count - len(df)

    # Referential integrity check
    df = df[df["movie_id"].isin(valid_movie_ids)]
    orphans_dropped = (initial_count - dedup_count - invalid_ratings_dropped) - len(df)

    clean_cols = ["user_id", "movie_id", "rating", "timestamp"]
    clean_df = df[clean_cols].copy()

    metrics = {
        "ratings_initial": initial_count,
        "ratings_cleaned": len(clean_df),
        "ratings_deduplicated": dedup_count,
        "ratings_invalid_dropped": invalid_ratings_dropped,
        "ratings_orphans_dropped": orphans_dropped
    }
    return clean_df, metrics


def run_cleaning(
    raw_movies: pd.DataFrame,
    raw_ratings: pd.DataFrame,
    genre_columns: List[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Execute complete cleaning step."""
    logger.info("=" * 60)
    logger.info("PIPELINE STEP 2: DATA CLEANING & NORMALIZATION")
    logger.info("=" * 60)

    clean_movies_df, movie_metrics = clean_movies(raw_movies)
    valid_movie_ids = set(clean_movies_df["movie_id"])
    clean_ratings_df, rating_metrics = clean_ratings(raw_ratings, valid_movie_ids)

    combined_metrics = {**movie_metrics, **rating_metrics}
    logger.info(
        f"[CLEANING COMPLETE] Movies: {combined_metrics['movies_cleaned']} (from {combined_metrics['movies_initial']}), "
        f"Ratings: {combined_metrics['ratings_cleaned']} (from {combined_metrics['ratings_initial']})"
    )
    return clean_movies_df, clean_ratings_df, combined_metrics

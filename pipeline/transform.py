"""
Pipeline Step 3: Feature Engineering & Transformation
------------------------------------------------------
Enriches clean movies and ratings into analytical and serving-ready dataframes:
- Computes rating counts and average ratings per movie
- Calculates a robust Bayesian weighted popularity score (IMDb formula)
- Constructs a rich feature_text representation for content-based vectorization
- Saves intermediate artifacts into data/processed/ (Parquet + CSV)
"""

import os
import re
import logging
from pathlib import Path
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger("pipeline.transform")


def calculate_ratings_summary(ratings_df: pd.DataFrame, m_threshold: int = 15) -> pd.DataFrame:
    """
    Compute aggregate rating statistics per movie and apply Bayesian shrinkage:
    Formula:
      W = (v / (v + m)) * R + (m / (v + m)) * C
    where:
      v = movie rating_count
      m = minimum votes threshold (default 15)
      R = movie avg_rating
      C = global mean rating
    """
    logger.info("Computing rating aggregations and Bayesian popularity scores...")

    global_mean = float(ratings_df["rating"].mean())
    logger.info(f"Global rating mean across all ratings: {global_mean:.4f}")

    agg = ratings_df.groupby("movie_id").agg(
        rating_count=("rating", "count"),
        avg_rating=("rating", "mean")
    ).reset_index()

    # Bayesian weighted rating
    v = agg["rating_count"]
    m = m_threshold
    R = agg["avg_rating"]
    C = global_mean

    agg["popularity_score"] = (v / (v + m)) * R + (m / (v + m)) * C
    agg["avg_rating"] = agg["avg_rating"].round(2)
    agg["popularity_score"] = agg["popularity_score"].round(3)

    return agg


def create_feature_text(title: str, genres: str, release_year: int) -> str:
    """
    Construct rich feature text representation for content-based TF-IDF vectorization.
    Combines stripped title, doubled genres for term frequency weighting, and release era.
    """
    # Remove year in parenthesis from title for keyword matching
    clean_t = re.sub(r"\s*\(\d{4}\)", "", title).strip()
    # Normalize genres into space-separated string
    genre_tokens = genres.replace("|", " ").replace("-", " ")
    # Repeat genres to give them higher semantic weight in TF-IDF
    features = f"{clean_t} {genre_tokens} {genre_tokens} {release_year}"
    return features.lower()


def run_transformation(
    clean_movies: pd.DataFrame,
    clean_ratings: pd.DataFrame,
    processed_dir: Path
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Execute complete transformation step."""
    logger.info("=" * 60)
    logger.info("PIPELINE STEP 3: FEATURE ENGINEERING & TRANSFORMATION")
    logger.info("=" * 60)

    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Rating summaries
    ratings_summary = calculate_ratings_summary(clean_ratings)

    # 2. Join movies with ratings summary (left join so movies with 0 ratings are retained)
    transformed_movies = clean_movies.merge(ratings_summary, on="movie_id", how="left")

    # Fill default for unrated movies
    global_mean = float(clean_ratings["rating"].mean())
    transformed_movies["avg_rating"] = transformed_movies["avg_rating"].fillna(0.0)
    transformed_movies["rating_count"] = transformed_movies["rating_count"].fillna(0).astype(int)
    transformed_movies["popularity_score"] = transformed_movies["popularity_score"].fillna(
        round(global_mean * 0.5, 3)
    )

    # 3. Create feature_text column
    transformed_movies["feature_text"] = transformed_movies.apply(
        lambda r: create_feature_text(r["title"], r["genres"], r["release_year"]),
        axis=1
    )

    # 4. Save processed artifacts as Parquet and CSV
    movies_parquet = processed_dir / "movies_processed.parquet"
    movies_csv = processed_dir / "movies_processed.csv"
    ratings_parquet = processed_dir / "ratings_summary.parquet"
    ratings_csv = processed_dir / "ratings_summary.csv"

    transformed_movies.to_parquet(movies_parquet, index=False)
    transformed_movies.to_csv(movies_csv, index=False)
    ratings_summary.to_parquet(ratings_parquet, index=False)
    ratings_summary.to_csv(ratings_csv, index=False)

    logger.info(f"Saved processed movies ({len(transformed_movies)} rows) to: {movies_parquet}")
    logger.info(f"Saved ratings summary ({len(ratings_summary)} rows) to: {ratings_parquet}")

    metrics = {
        "transformed_movies_count": len(transformed_movies),
        "movies_with_ratings": len(ratings_summary),
        "mean_rating_count": round(float(ratings_summary["rating_count"].mean()), 2),
        "max_rating_count": int(ratings_summary["rating_count"].max()),
        "global_rating_mean": round(global_mean, 2)
    }
    return transformed_movies, ratings_summary, metrics

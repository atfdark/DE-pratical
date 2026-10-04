"""
Pipeline Step 4: Recommendation Generation Engine
-------------------------------------------------
Precomputes Content-Based Recommendations using TF-IDF vectorization
and pairwise Cosine Similarity over movie metadata features.
Also generates global Top-K popular movies for cold-start fallback.
"""

import logging
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("pipeline.recommend")


def compute_content_recommendations(
    movies_df: pd.DataFrame,
    top_k: int = 15
) -> pd.DataFrame:
    """
    Generate Top-K content-based recommendations for each movie.
    - Vectorizes 'feature_text' using TF-IDF (1-2 ngrams, sublinear tf)
    - Calculates Cosine Similarity matrix
    - Extracts Top-K most similar movies per item, excluding self-matches
    """
    logger.info("Vectorizing metadata using TF-IDF (sublinear_tf=True, ngram_range=(1,2))...")

    # Fit TF-IDF on feature_text
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1
    )
    tfidf_matrix = vectorizer.fit_transform(movies_df["feature_text"])
    logger.info(f"TF-IDF matrix computed: shape={tfidf_matrix.shape}")

    logger.info("Computing pairwise cosine similarity matrix...")
    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

    movie_ids = movies_df["movie_id"].values
    n_movies = len(movie_ids)
    logger.info(f"Extracting top {top_k} recommendations for {n_movies} movies...")

    records = []
    for idx in range(n_movies):
        source_id = int(movie_ids[idx])
        sim_scores = similarity_matrix[idx].copy()
        sim_scores[idx] = -1.0  # Zero out self-similarity

        # Get indices of top_k highest similarity scores
        top_indices = np.argsort(sim_scores)[::-1][:top_k]

        rank = 1
        for target_idx in top_indices:
            score = float(sim_scores[target_idx])
            if score <= 0.0:
                continue  # Discard negative/zero similarities

            target_id = int(movie_ids[target_idx])
            records.append({
                "movie_id": source_id,
                "recommended_movie_id": target_id,
                "rank": rank,
                "similarity_score": round(score, 4)
            })
            rank += 1

    rec_df = pd.DataFrame(records)
    logger.info(f"Generated {len(rec_df)} precomputed recommendation records")
    return rec_df


def compute_popular_movies(
    movies_df: pd.DataFrame,
    top_n: int = 50
) -> pd.DataFrame:
    """
    Generate ranked list of Top-N popular movies based on Bayesian popularity score.
    Used for general browsing and cold-start fallback.
    """
    logger.info(f"Computing top {top_n} popular movies fallback list...")
    sorted_df = movies_df.sort_values(by="popularity_score", ascending=False).reset_index(drop=True)

    popular_records = []
    for rank, (_, row) in enumerate(sorted_df.head(top_n).iterrows(), start=1):
        popular_records.append({
            "movie_id": int(row["movie_id"]),
            "rank": rank,
            "popularity_score": round(float(row["popularity_score"]), 3)
        })

    pop_df = pd.DataFrame(popular_records)
    logger.info(f"Generated {len(pop_df)} popular movies ranking records")
    return pop_df


def run_recommendations(
    transformed_movies: pd.DataFrame,
    top_k: int = 15,
    top_popular: int = 50
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Execute complete recommendation precomputation step."""
    logger.info("=" * 60)
    logger.info("PIPELINE STEP 4: RECOMMENDATION ENGINE COMPUTATION")
    logger.info("=" * 60)

    recommendations_df = compute_content_recommendations(transformed_movies, top_k=top_k)
    popular_movies_df = compute_popular_movies(transformed_movies, top_n=top_popular)

    avg_score = float(recommendations_df["similarity_score"].mean()) if not recommendations_df.empty else 0.0

    metrics = {
        "total_recommendations": len(recommendations_df),
        "movies_with_recommendations": int(recommendations_df["movie_id"].nunique()),
        "avg_similarity_score": round(avg_score, 4),
        "total_popular_movies": len(popular_movies_df)
    }
    logger.info(
        f"[RECOMMENDATIONS COMPLETE] {metrics['total_recommendations']} rows generated, "
        f"average similarity: {metrics['avg_similarity_score']}"
    )
    return recommendations_df, popular_movies_df, metrics

"""
End-to-End Movie Data Pipeline CLI
-----------------------------------
Runs the complete data engineering & recommendation precomputation pipeline:
1. Ingestion & Validation
2. Cleaning & Normalization
3. Feature Engineering & Bayesian Aggregation
4. TF-IDF & Cosine Similarity Precomputation
5. DuckDB Analytical Serving Store & Parquet Generation
6. Integrity & Latency Validation
7. Summary Report
"""

import sys
import time
import logging
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.download_data import download_and_extract, verify_dataset
from pipeline.ingest import run_ingestion
from pipeline.clean import run_cleaning
from pipeline.transform import run_transformation
from pipeline.recommend import run_recommendations
from pipeline.build_serving_data import run_serving_data_build

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("run_pipeline")


def run_pipeline():
    start_time = time.time()
    logger.info("Starting Movie Recommendation Data Pipeline...")

    raw_dir = BASE_DIR / "data" / "raw" / "ml-latest-small"
    processed_dir = BASE_DIR / "data" / "processed"
    serving_dir = BASE_DIR / "data" / "serving"
    serving_db_path = serving_dir / "movies.duckdb"

    # Step 1: Ingestion
    raw_movies, raw_ratings, raw_users, ingest_metrics = run_ingestion(raw_dir)

    # Step 2: Cleaning
    clean_movies, clean_ratings, clean_metrics = run_cleaning(raw_movies, raw_ratings)

    # Step 3: Transformation
    transformed_movies, ratings_summary, transform_metrics = run_transformation(
        clean_movies, clean_ratings, processed_dir
    )

    # Step 4: Recommendation Precomputation
    recommendations, popular_movies, rec_metrics = run_recommendations(
        transformed_movies, top_k=100, top_popular=50
    )

    # Step 5: Serving Data Layer (DuckDB + Parquet)
    serving_metrics = run_serving_data_build(
        transformed_movies=transformed_movies,
        ratings_summary=ratings_summary,
        recommendations=recommendations,
        popular_movies=popular_movies,
        serving_db_path=serving_db_path,
        parquet_dir=serving_dir
    )

    total_duration = time.time() - start_time

    # Print Summary Report
    print("\n" + "=" * 60)
    print("           MOVIE DATA PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Movies processed:          {clean_metrics['movies_cleaned']:,}")
    print(f"Ratings processed:         {clean_metrics['ratings_cleaned']:,}")
    print(f"Total genres available:    {ingest_metrics.get('genre_count', 'N/A')} (Dynamic from ML-latest)")
    print(f"Recommendations generated: {rec_metrics['total_recommendations']:,}")
    print(f"Popular movies indexed:    {rec_metrics['total_popular_movies']:,}")
    print(f"Serving tables created:    4 (movies, ratings_summary, recommendations, popular_movies)")
    print(f"Serving Database:          {serving_db_path}")
    print(f"Sample Query Latency:      {serving_metrics['sample_query_latency_ms']} ms")
    print(f"Total Pipeline Runtime:    {total_duration:.2f} seconds")
    print(f"Status:                    SUCCESS")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_pipeline()

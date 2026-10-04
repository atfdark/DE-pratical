"""
Pipeline Step 5: Serving Data Layer Generation
----------------------------------------------
Ingests processed dataframes into high-performance analytical storage:
- Creates DuckDB database at data/serving/movies.duckdb
- Builds optimized tables with primary keys:
    1. movies
    2. ratings_summary
    3. recommendations
    4. popular_movies
- Creates secondary indexes for sub-millisecond query latency
- Exports Parquet backups into data/serving/
- Performs referential verification queries
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any
import duckdb
import pandas as pd

logger = logging.getLogger("pipeline.serving")


def build_duckdb_serving_store(
    movies_df: pd.DataFrame,
    ratings_summary_df: pd.DataFrame,
    recommendations_df: pd.DataFrame,
    popular_movies_df: pd.DataFrame,
    serving_db_path: Path,
    parquet_dir: Path
) -> Dict[str, Any]:
    """Populate DuckDB database and export Parquet serving tables."""
    logger.info("Initializing DuckDB analytical serving store...")

    serving_db_path.parent.mkdir(parents=True, exist_ok=True)
    parquet_dir.mkdir(parents=True, exist_ok=True)

    # Remove stale database file if rebuilding
    if serving_db_path.exists():
        try:
            serving_db_path.unlink()
        except Exception as e:
            logger.warning(f"Could not remove existing db file: {e}")

    con = duckdb.connect(str(serving_db_path))

    # 1. Create table `movies`
    logger.info("Building 'movies' serving table...")
    con.execute("""
        CREATE TABLE movies (
            movie_id INTEGER PRIMARY KEY,
            title VARCHAR NOT NULL,
            genres VARCHAR NOT NULL,
            release_year INTEGER
        );
    """)
    movie_subset = movies_df[["movie_id", "title", "genres", "release_year"]].drop_duplicates("movie_id")
    con.register("df_movies", movie_subset)
    con.execute("INSERT INTO movies SELECT * FROM df_movies;")

    # 2. Create table `ratings_summary`
    logger.info("Building 'ratings_summary' serving table...")
    con.execute("""
        CREATE TABLE ratings_summary (
            movie_id INTEGER PRIMARY KEY,
            avg_rating DOUBLE NOT NULL,
            rating_count INTEGER NOT NULL,
            popularity_score DOUBLE NOT NULL
        );
    """)
    con.register("df_ratings", ratings_summary_df[["movie_id", "avg_rating", "rating_count", "popularity_score"]])
    con.execute("INSERT INTO ratings_summary SELECT * FROM df_ratings;")

    # 3. Create table `recommendations`
    logger.info("Building 'recommendations' serving table...")
    con.execute("""
        CREATE TABLE recommendations (
            movie_id INTEGER NOT NULL,
            recommended_movie_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            similarity_score DOUBLE NOT NULL,
            PRIMARY KEY (movie_id, rank)
        );
    """)
    con.register("df_rec", recommendations_df[["movie_id", "recommended_movie_id", "rank", "similarity_score"]])
    con.execute("INSERT INTO recommendations SELECT * FROM df_rec;")

    # 4. Create table `popular_movies`
    logger.info("Building 'popular_movies' serving table...")
    con.execute("""
        CREATE TABLE popular_movies (
            movie_id INTEGER PRIMARY KEY,
            rank INTEGER NOT NULL,
            popularity_score DOUBLE NOT NULL
        );
    """)
    con.register("df_pop", popular_movies_df[["movie_id", "rank", "popularity_score"]])
    con.execute("INSERT INTO popular_movies SELECT * FROM df_pop;")

    # 5. Build Performance Indexes
    logger.info("Creating serving performance indexes...")
    con.execute("CREATE INDEX idx_movies_title ON movies (lower(title));")
    con.execute("CREATE INDEX idx_rec_movie_id ON recommendations (movie_id);")
    con.execute("CREATE INDEX idx_rec_lookup ON recommendations (movie_id, rank);")
    con.execute("CREATE INDEX idx_pop_rank ON popular_movies (rank);")

    # 6. Export Parquet representations
    logger.info("Exporting serving tables to Parquet format...")
    parquet_files = {
        "movies": parquet_dir / "movies.parquet",
        "ratings_summary": parquet_dir / "ratings_summary.parquet",
        "recommendations": parquet_dir / "recommendations.parquet",
        "popular_movies": parquet_dir / "popular_movies.parquet"
    }

    for table, file_path in parquet_files.items():
        # Escape path for SQL
        escaped_path = str(file_path).replace("\\", "/")
        con.execute(f"COPY {table} TO '{escaped_path}' (FORMAT PARQUET);")

    # 7. Verification & Sanity queries
    logger.info("Executing verification queries on serving tables...")
    t0 = time.perf_counter()
    sample_res = con.execute("""
        SELECT
            r.rank,
            m.movie_id,
            m.title,
            m.genres,
            s.avg_rating,
            r.similarity_score
        FROM recommendations r
        JOIN movies m ON r.recommended_movie_id = m.movie_id
        LEFT JOIN ratings_summary s ON m.movie_id = s.movie_id
        WHERE r.movie_id = 1
        ORDER BY r.rank ASC
        LIMIT 5;
    """).fetchall()
    latency_ms = (time.perf_counter() - t0) * 1000

    row_counts = {
        "movies": con.execute("SELECT COUNT(*) FROM movies;").fetchone()[0],
        "ratings_summary": con.execute("SELECT COUNT(*) FROM ratings_summary;").fetchone()[0],
        "recommendations": con.execute("SELECT COUNT(*) FROM recommendations;").fetchone()[0],
        "popular_movies": con.execute("SELECT COUNT(*) FROM popular_movies;").fetchone()[0],
    }

    con.close()

    metrics = {
        "database_path": str(serving_db_path),
        "row_counts": row_counts,
        "sample_query_latency_ms": round(latency_ms, 3),
        "sample_query_results": len(sample_res),
        "parquet_files": [str(p) for p in parquet_files.values()]
    }
    logger.info(f"Serving store successfully built: {row_counts}")
    logger.info(f"Sample recommendation query execution time: {metrics['sample_query_latency_ms']} ms")
    return metrics


def run_serving_data_build(
    transformed_movies: pd.DataFrame,
    ratings_summary: pd.DataFrame,
    recommendations: pd.DataFrame,
    popular_movies: pd.DataFrame,
    serving_db_path: Path,
    parquet_dir: Path
) -> Dict[str, Any]:
    """Execute complete serving data build step."""
    logger.info("=" * 60)
    logger.info("PIPELINE STEP 5: SERVING DATA STORE GENERATION")
    logger.info("=" * 60)

    metrics = build_duckdb_serving_store(
        movies_df=transformed_movies,
        ratings_summary_df=ratings_summary,
        recommendations_df=recommendations,
        popular_movies_df=popular_movies,
        serving_db_path=serving_db_path,
        parquet_dir=parquet_dir
    )
    return metrics

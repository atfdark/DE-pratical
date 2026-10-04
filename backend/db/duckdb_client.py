"""
DuckDB Client & Query Manager
-----------------------------
High-performance, thread-safe access layer to DuckDB analytical serving store.
Provides parameterized execution, row-to-dictionary mapping, and query latency tracking.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import duckdb

from backend.config import settings

logger = logging.getLogger("backend.duckdb")


class DuckDBClient:
    """Manages read-only connection to DuckDB analytical serving database."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH
        self._con = None

    def get_connection(self):
        """Obtain or reopen read-only database connection."""
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"DuckDB serving database not found at: {self.db_path}. "
                "Please run 'python scripts/run_pipeline.py' first."
            )
        # Using connect per thread or shared read_only connection
        # In DuckDB, read_only=True supports concurrent readers
        try:
            con = duckdb.connect(str(self.db_path), read_only=True)
            return con
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise

    def query(self, sql: str, params: Optional[List[Any]] = None) -> Tuple[List[Dict[str, Any]], float]:
        """
        Execute a parameterized SQL query against DuckDB.
        Returns:
            Tuple of (list_of_row_dictionaries, execution_time_ms)
        """
        params = params or []
        t0 = time.perf_counter()
        con = self.get_connection()
        try:
            cursor = con.execute(sql, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            latency_ms = (time.perf_counter() - t0) * 1000

            results = [dict(zip(columns, row)) for row in rows]
            return results, round(latency_ms, 3)
        finally:
            con.close()

    def query_one(self, sql: str, params: Optional[List[Any]] = None) -> Tuple[Optional[Dict[str, Any]], float]:
        """Execute query returning a single row or None."""
        results, latency_ms = self.query(sql, params)
        return (results[0] if results else None), latency_ms

    def health_check(self) -> Dict[str, Any]:
        """Check database accessibility and record counts."""
        if not self.db_path.exists():
            return {"status": "error", "message": "Database file not found"}

        try:
            con = self.get_connection()
            movie_count = con.execute("SELECT COUNT(*) FROM movies;").fetchone()[0]
            rec_count = con.execute("SELECT COUNT(*) FROM recommendations;").fetchone()[0]
            con.close()
            return {
                "status": "healthy",
                "database_path": str(self.db_path),
                "movies_count": movie_count,
                "recommendations_count": rec_count
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global client instance
db_client = DuckDBClient()

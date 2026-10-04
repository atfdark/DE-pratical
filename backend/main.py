"""
Main FastAPI Application Entrypoint
-----------------------------------
Data Serving Layer for Movie Recommendation System.
Provides low-latency HTTP access to precomputed analytical DuckDB serving tables.
"""

import time
from datetime import datetime, timezone
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.db.duckdb_client import db_client
from backend.models.schemas import HealthResponse
from backend.api import movies, recommendations, stats, media

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("backend.main")

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "**College Data Engineering Practical: Serving Data for Analytics & ML**\n\n"
        "This API implements the **Data Serving Layer** separating heavy offline data processing "
        "(ETL, TF-IDF vectorization, Bayesian shrinkage) from online low-latency consumption. "
        "All recommendations are served from precomputed analytical DuckDB tables."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response


# Include Routers
app.include_router(media.router)
app.include_router(movies.router)
app.include_router(recommendations.router)
app.include_router(stats.router)


@app.get(
    "/",
    response_model=HealthResponse,
    tags=["Health & Status"],
    summary="Data Serving API Health Check"
)
def root_health():
    """Verify backend operational status, DuckDB serving database accessibility, and record counts."""
    health = db_client.health_check()
    return HealthResponse(
        status=health.get("status", "healthy"),
        database=str(settings.DB_PATH),
        movies_count=health.get("movies_count", 0),
        recommendations_count=health.get("recommendations_count", 0),
        timestamp=datetime.now(timezone.utc).isoformat()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

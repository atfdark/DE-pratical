"""
Pydantic Request & Response Data Models
---------------------------------------
Strongly-typed schemas ensuring API contracts, documentation, and data validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Movie(BaseModel):
    movie_id: int = Field(..., description="Unique movie identifier", examples=[1])
    title: str = Field(..., description="Full movie title", examples=["Toy Story (1995)"])
    genres: str = Field(..., description="Pipe-separated genres", examples=["Animation|Children's|Comedy"])
    release_year: Optional[int] = Field(None, description="Release year", examples=[1995])
    avg_rating: float = Field(0.0, description="Mean rating from 1.0 to 5.0", examples=[3.88])
    rating_count: int = Field(0, description="Total number of ratings received", examples=[452])
    popularity_score: float = Field(0.0, description="Bayesian weighted score", examples=[3.86])


class MovieListResponse(BaseModel):
    total: int = Field(..., description="Total matching movies", examples=[1682])
    page: int = Field(1, description="Current page number", examples=[1])
    page_size: int = Field(20, description="Results per page", examples=[20])
    results: List[Movie] = Field(..., description="List of movie records")
    execution_time_ms: float = Field(..., description="DuckDB query execution time in ms", examples=[3.4])


class SearchResponse(BaseModel):
    query: str = Field(..., description="Search keyword", examples=["Star Wars"])
    count: int = Field(..., description="Number of matches found", examples=[1])
    results: List[Movie] = Field(..., description="List of matching movies")
    execution_time_ms: float = Field(..., description="Search query execution time in ms", examples=[2.1])


class RecommendationItem(BaseModel):
    movie_id: int = Field(..., description="Recommended movie identifier", examples=[96])
    title: str = Field(..., description="Recommended movie title", examples=["Terminator 2: Judgment Day (1991)"])
    genres: str = Field(..., description="Recommended movie genres", examples=["Action|Sci-Fi|Thriller"])
    release_year: Optional[int] = Field(None, description="Release year", examples=[1991])
    avg_rating: float = Field(..., description="Average rating", examples=[4.0])
    rating_count: int = Field(..., description="Rating count", examples=[295])
    popularity_score: float = Field(..., description="Bayesian popularity score", examples=[3.98])
    rank: int = Field(..., description="Recommendation position rank", examples=[1])
    similarity_score: float = Field(..., description="TF-IDF Cosine similarity score [0.0 - 1.0]", examples=[0.68])


class RecommendationResponse(BaseModel):
    source_movie: Movie = Field(..., description="Target movie details")
    count: int = Field(..., description="Number of recommendations returned", examples=[10])
    is_fallback: bool = Field(False, description="Whether fallback recommendations were used", examples=[False])
    fallback_reason: Optional[str] = Field(None, description="Explanation if fallback was activated")
    results: List[RecommendationItem] = Field(..., description="Ranked list of recommendations")
    processing_time_ms: float = Field(..., description="Total serving response latency in milliseconds", examples=[4.5])


class PopularMovieItem(BaseModel):
    movie_id: int = Field(..., description="Movie identifier", examples=[50])
    title: str = Field(..., description="Movie title", examples=["Star Wars (1977)"])
    genres: str = Field(..., description="Movie genres", examples=["Action|Adventure|Romance|Sci-Fi|War"])
    release_year: Optional[int] = Field(None, description="Release year", examples=[1977])
    avg_rating: float = Field(..., description="Average rating", examples=[4.36])
    rating_count: int = Field(..., description="Rating count", examples=[583])
    popularity_score: float = Field(..., description="Bayesian popularity score", examples=[4.338])
    rank: int = Field(..., description="Popularity rank", examples=[1])


class PopularResponse(BaseModel):
    count: int = Field(..., description="Number of popular movies returned", examples=[20])
    results: List[PopularMovieItem] = Field(..., description="Ranked popular movies")
    execution_time_ms: float = Field(..., description="Query execution time in ms", examples=[1.8])


class GenreStats(BaseModel):
    genre: str = Field(..., description="Genre name", examples=["Action"])
    count: int = Field(..., description="Number of movies in genre", examples=[251])
    avg_rating: float = Field(..., description="Average rating for genre", examples=[3.48])


class RatingDistributionItem(BaseModel):
    rating: int = Field(..., description="Star rating value (1-5)", examples=[4])
    count: int = Field(..., description="Total frequency of rating", examples=[34174])


class DatasetStatsResponse(BaseModel):
    total_movies: int = Field(..., description="Total movies in serving database", examples=[1682])
    total_ratings: int = Field(..., description="Total ratings in dataset", examples=[100000])
    average_rating: float = Field(..., description="Overall average rating across all ratings", examples=[3.53])
    total_genres: int = Field(..., description="Number of distinct genres", examples=[19])
    genres: List[GenreStats] = Field(..., description="Genre breakdown statistics")
    rating_distribution: List[RatingDistributionItem] = Field(..., description="Rating histogram counts")
    top_rated: List[PopularMovieItem] = Field(..., description="Top rated movies by Bayesian score")
    most_rated: List[PopularMovieItem] = Field(..., description="Most frequently rated movies")
    execution_time_ms: float = Field(..., description="Analytics query aggregation time in ms", examples=[8.2])


class HealthResponse(BaseModel):
    status: str = Field("healthy", examples=["healthy"])
    database: str = Field(..., examples=["data/serving/movies.duckdb"])
    movies_count: int = Field(..., examples=[1682])
    recommendations_count: int = Field(..., examples=[25213])
    timestamp: str = Field(..., examples=["2026-10-03T18:00:00Z"])


class RecommendRequest(BaseModel):
    movie_id: Optional[int] = Field(None, description="Source movie ID to get recommendations for", examples=[1])
    title: Optional[str] = Field(None, description="Optional title lookup if ID unknown", examples=["Star Wars"])
    top_k: int = Field(10, description="Number of recommendations requested", ge=1, le=100, examples=[10])

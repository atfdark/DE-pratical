"""
Media API Endpoints
-------------------
Serves TMDB-enriched presentation metadata and proxied/cached images.
The browser never calls TMDB directly.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from backend.services.data_service import data_service
from backend.services.media_service import media_service

router = APIRouter(tags=["Media Enrichment"])


def _image_url(size: str, path: str | None) -> str | None:
    return f"/api/media/image/{size}/{path.lstrip('/')}" if path else None


@router.get(
    "/api/movies/{movie_id}/media",
    summary="Get Movie Artwork & Description",
    description="Poster, backdrop, overview, cast and trailer for a MovieLens movie (TMDB enrichment, cached)."
)
def get_movie_media(movie_id: int):
    movie, _ = data_service.get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Movie {movie_id} not found.")

    m = media_service.get_media(movie.movie_id, movie.title, getattr(movie, "release_year", None))
    return {
        "movie_id": movie.movie_id,
        "title": movie.title,
        "found": m.get("found", False),
        "tmdb_id": m.get("tmdb_id"),
        "poster_url": _image_url("w500", m.get("poster_path")),
        "backdrop_url": _image_url("w1280", m.get("backdrop_path")),
        "overview": m.get("overview", ""),
        "tagline": m.get("tagline", ""),
        "runtime": m.get("runtime"),
        "tmdb_rating": m.get("tmdb_rating"),
        "director": m.get("director", ""),
        "cast": m.get("cast", []),
        "trailer_key": m.get("trailer_key"),
        "reason": m.get("reason"),
    }


@router.get("/api/media/image/{size}/{filename}", include_in_schema=False)
def get_media_image(size: str, filename: str):
    path = media_service.get_image(size, filename)
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not available.")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=604800"})

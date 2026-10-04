"""
TMDB Enrichment Batch Job
-------------------------
Pre-warms the media enrichment cache (posters, backdrops, descriptions, cast,
trailers) for every movie in the MovieLens serving catalog.

This is an OPTIONAL enrichment stage. It never modifies the MovieLens source or
the serving tables; results go to data/serving/tmdb_cache/metadata.json.

Usage:
    python scripts/enrich_tmdb.py              # metadata for all movies
    python scripts/enrich_tmdb.py --images     # also download w500 posters locally
    python scripts/enrich_tmdb.py --refresh    # ignore existing cache
"""

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import settings  # noqa: E402
from backend.services.media_service import media_service  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", action="store_true", help="Download poster images too")
    ap.add_argument("--refresh", action="store_true", help="Re-fetch even if cached")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    if not settings.TMDB_API_KEY:
        print("ERROR: TMDB_API_KEY is not set. Add it to the project root .env file.")
        sys.exit(1)

    movies = pd.read_parquet(settings.PARQUET_DIR / "movies.parquet")
    year_col = "release_year" if "release_year" in movies.columns else None
    if args.refresh:
        media_service._cache.clear()

    todo = [r for _, r in movies.iterrows() if str(int(r["movie_id"])) not in media_service._cache]
    print(f"Catalog: {len(movies)} movies | already cached: {len(movies) - len(todo)} | to fetch: {len(todo)}")

    t0, done, found = time.time(), 0, 0

    def work(row):
        year = int(row[year_col]) if year_col and pd.notna(row[year_col]) else None
        rec = media_service.get_media(int(row["movie_id"]), row["title"], year, persist=False)
        if args.images and rec.get("poster_path"):
            media_service.get_image("w500", rec["poster_path"].lstrip("/"))
        return rec

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for fut in as_completed([pool.submit(work, r) for r in todo]):
            done += 1
            found += int(bool(fut.result().get("found")))
            if done % 100 == 0 or done == len(todo):
                media_service.flush()
                print(f"  {done}/{len(todo)} processed, {found} matched ({time.time() - t0:.0f}s)")

    media_service.flush()
    total_found = sum(1 for v in media_service._cache.values() if v.get("found"))
    print(f"\nDone. Coverage: {total_found}/{len(movies)} movies have TMDB artwork "
          f"({100 * total_found / len(movies):.1f}%).")


if __name__ == "__main__":
    main()

"""
Media Enrichment Service (TMDB)
-------------------------------
Enriches MovieLens catalog entries with external presentation metadata
(poster, backdrop, overview, cast, trailer) from The Movie Database (TMDB).

Design notes (Data Engineering):
- The MovieLens source data is NEVER modified. Enrichment lives in a separate
  cache layer: data/serving/tmdb_cache/ (metadata.json + images/).
- The backend acts as a gateway: the browser only talks to our own API, so
  TMDB being blocked by ad-blockers / ISP DNS / CORS does not break the UI.
- Results (including "not found") are cached, so each movie hits TMDB at most once.
  Run `python scripts/enrich_tmdb.py` to pre-warm the cache for the full catalog.
"""

import json
import logging
import re
import threading
from pathlib import Path
from typing import Dict, List, Optional

import requests

from backend.config import settings

logger = logging.getLogger("backend.media")

TMDB_API = "https://api.themoviedb.org/3"
TMDB_IMG = "https://image.tmdb.org/t/p"
ALLOWED_SIZES = {"w185", "w342", "w500", "w780", "w1280", "original"}
_ARTICLES = r"The|A|An|Les|La|Le|L'|Il|Das|Der|Die|El"


def parse_movielens_title(raw: str) -> Dict:
    """
    'Usual Suspects, The (1995)' -> {'year': 1995, 'candidates': ['The Usual Suspects', ...]}
    'Seven (Se7en) (1995)'       -> candidates ['Seven', 'Se7en']
    """
    year_match = re.search(r"\((\d{4})\)\s*$", raw)
    year = int(year_match.group(1)) if year_match else None
    base = re.sub(r"\s*\(\d{4}\)\s*$", "", raw).strip()

    def fix_article(t: str) -> str:
        m = re.match(rf"^(.*),\s*({_ARTICLES})$", t.strip(), re.IGNORECASE)
        if not m:
            return t.strip()
        art = m.group(2)
        return f"{art}{m.group(1)}" if art.endswith("'") else f"{art} {m.group(1)}"

    alts = re.findall(r"\(([^)]+)\)", base)
    main = re.sub(r"\s*\([^)]*\)", "", base).strip()

    candidates: List[str] = [fix_article(main), main]
    for alt in alts:
        alt = re.sub(r"^a\.k\.a\.?\s*", "", alt, flags=re.IGNORECASE)
        candidates.append(fix_article(alt))

    seen, unique = set(), []
    for c in candidates:
        if c and c.lower() not in seen:
            seen.add(c.lower())
            unique.append(c)
    return {"year": year, "candidates": unique}


class MediaService:
    def __init__(self):
        self.cache_dir: Path = settings.PARQUET_DIR / "tmdb_cache"
        self.image_dir: Path = self.cache_dir / "images"
        self.meta_file: Path = self.cache_dir / "metadata.json"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._session = requests.Session()
        self._cache: Dict[str, Dict] = self._load()

    # ---------- cache persistence ----------
    def _load(self) -> Dict[str, Dict]:
        self._mtime = 0.0
        if self.meta_file.exists():
            try:
                self._mtime = self.meta_file.stat().st_mtime
                return json.loads(self.meta_file.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("TMDB metadata cache corrupted, starting fresh.")
        return {}

    def _refresh_if_changed(self):
        """Pick up entries written by scripts/enrich_tmdb.py while the API is running."""
        if self.meta_file.exists() and self.meta_file.stat().st_mtime > self._mtime:
            disk = self._load()
            disk.update(self._cache)
            self._cache = disk

    def _save(self):
        self._refresh_if_changed()  # merge, never clobber other writers
        tmp = self.meta_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._cache, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.meta_file)
        self._mtime = self.meta_file.stat().st_mtime

    @property
    def enabled(self) -> bool:
        return bool(settings.TMDB_API_KEY)

    # ---------- TMDB calls ----------
    def _get(self, path: str, **params) -> Optional[Dict]:
        params["api_key"] = settings.TMDB_API_KEY
        try:
            r = self._session.get(f"{TMDB_API}{path}", params=params, timeout=10)
            if r.status_code == 200:
                return r.json()
            logger.warning("TMDB %s -> HTTP %s", path, r.status_code)
        except requests.RequestException as e:
            logger.warning("TMDB request failed: %s", e)
        return None

    @staticmethod
    def _norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", (s or "").lower())

    def _score(self, r: Dict, candidates: List[str], year: Optional[int]) -> float:
        names = {self._norm(r.get("title")), self._norm(r.get("original_title"))}
        score = 0.0
        if any(self._norm(c) in names for c in candidates):
            score += 10
        rd = (r.get("release_date") or "")[:4]
        if year and rd.isdigit():
            diff = abs(int(rd) - year)
            score += 6 if diff == 0 else 3 if diff == 1 else -5
        score += min(r.get("vote_count", 0), 5000) / 1000  # popularity tie-break (max +5)
        if not r.get("poster_path"):
            score -= 3
        return score

    def _search(self, title: str, year: Optional[int]) -> Optional[Dict]:
        parsed = parse_movielens_title(title)
        year = year or parsed["year"]
        candidates = parsed["candidates"]
        pool: Dict[int, Dict] = {}

        for query in candidates:
            data = self._get("/search/movie", query=query, year=year) if year else None
            for r in (data or {}).get("results", [])[:10]:
                pool[r["id"]] = r

        best = max(pool.values(), key=lambda r: self._score(r, candidates, year), default=None)
        if best and self._score(best, candidates, year) >= 12:
            return best

        # Fallback: search without year (release dates in MovieLens can differ slightly)
        for query in candidates[:2]:
            data = self._get("/search/movie", query=query)
            for r in (data or {}).get("results", [])[:10]:
                pool[r["id"]] = r
        best = max(pool.values(), key=lambda r: self._score(r, candidates, year), default=None)
        return best if best and self._score(best, candidates, year) > 0 else None

    def _build(self, movie_id: int, title: str, year: Optional[int]) -> Dict:
        hit = self._search(title, year)
        if not hit:
            return {"movie_id": movie_id, "found": False}

        details = self._get(f"/movie/{hit['id']}", append_to_response="credits,videos") or {}
        videos = (details.get("videos") or {}).get("results") or []
        trailer = next((v for v in videos if v.get("site") == "YouTube" and v.get("type") == "Trailer"), None) \
            or next((v for v in videos if v.get("site") == "YouTube"), None)
        credits = details.get("credits") or {}
        director = next((c["name"] for c in credits.get("crew", []) if c.get("job") == "Director"), "")

        return {
            "movie_id": movie_id,
            "found": True,
            "tmdb_id": hit["id"],
            "tmdb_title": hit.get("title"),
            "poster_path": hit.get("poster_path"),
            "backdrop_path": hit.get("backdrop_path") or details.get("backdrop_path"),
            "overview": details.get("overview") or hit.get("overview") or "",
            "tagline": details.get("tagline") or "",
            "runtime": details.get("runtime"),
            "tmdb_rating": hit.get("vote_average"),
            "director": director,
            "cast": [c["name"] for c in credits.get("cast", [])[:8]],
            "trailer_key": trailer["key"] if trailer else None,
        }

    # ---------- public API ----------
    def get_media(self, movie_id: int, title: str, year: Optional[int] = None, persist: bool = True) -> Dict:
        key = str(movie_id)
        with self._lock:
            if key not in self._cache:
                self._refresh_if_changed()
            if key in self._cache:
                return self._cache[key]
        if not self.enabled:
            return {"movie_id": movie_id, "found": False, "reason": "TMDB_API_KEY not configured"}

        record = self._build(movie_id, title, year)
        with self._lock:
            self._cache[key] = record
            if persist:
                self._save()
        return record

    def flush(self):
        with self._lock:
            self._save()

    def get_image(self, size: str, filename: str) -> Optional[Path]:
        """Download-once image proxy. Returns local file path or None."""
        if size not in ALLOWED_SIZES or not re.fullmatch(r"[A-Za-z0-9_\-]+\.(jpg|jpeg|png|webp)", filename):
            return None
        local = self.image_dir / size / filename
        if local.exists():
            return local
        try:
            r = self._session.get(f"{TMDB_IMG}/{size}/{filename}", timeout=15)
            if r.status_code != 200:
                return None
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(r.content)
            return local
        except requests.RequestException as e:
            logger.warning("TMDB image fetch failed: %s", e)
            return None


media_service = MediaService()

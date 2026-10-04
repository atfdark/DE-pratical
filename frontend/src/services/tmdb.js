/**
 * Media Service (artwork + descriptions)
 * --------------------------------------
 * Fetches poster/backdrop/overview/cast/trailer from OUR backend
 * (`/api/movies/{id}/media`). The backend talks to TMDB and caches results,
 * so the browser never calls TMDB directly (avoids ad-blocker / ISP / CORS issues).
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8080';
const cache = new Map();

const abs = (url) => (url ? `${API_BASE}${url}` : null);

/**
 * @param {{movie_id:number, title:string}} movie
 * @returns {Promise<{found:boolean, poster:string|null, backdrop:string|null, overview:string,
 *   tagline:string, runtime:number|null, tmdbRating:number|null, director:string,
 *   cast:string[], trailerKey:string|null}>}
 */
export function getMovieMedia(movie) {
  const id = movie?.movie_id;
  if (id == null) return Promise.resolve(emptyMedia());
  if (cache.has(id)) return cache.get(id);

  const p = fetch(`${API_BASE}/api/movies/${id}/media`)
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
    .then((d) => ({
      found: !!d.found,
      poster: abs(d.poster_url),
      backdrop: abs(d.backdrop_url) || abs(d.poster_url),
      overview: d.overview || '',
      tagline: d.tagline || '',
      runtime: d.runtime || null,
      tmdbRating: d.tmdb_rating || null,
      director: d.director || '',
      cast: d.cast || [],
      trailerKey: d.trailer_key || null,
    }))
    .catch((err) => {
      console.warn(`Media lookup failed for movie ${id}:`, err);
      cache.delete(id); // allow retry later
      return emptyMedia();
    });

  cache.set(id, p);
  return p;
}

function emptyMedia() {
  return {
    found: false, poster: null, backdrop: null, overview: '', tagline: '',
    runtime: null, tmdbRating: null, director: '', cast: [], trailerKey: null,
  };
}

/** Strip "(1995)" and fix "Usual Suspects, The" -> "The Usual Suspects" for display. */
export function displayTitle(raw = '') {
  let t = raw.replace(/\s*\(\d{4}\)\s*$/, '').trim();
  const m = t.match(/^(.*?),\s*(The|A|An)(\s*\(.*\))?$/i);
  if (m) t = `${m[2]} ${m[1]}${m[3] || ''}`;
  return t;
}

import React, { useState, useEffect } from 'react';
import { getMovieMedia } from '../services/tmdb';
import MovieDetailsModal from './MovieDetailsModal';

export default function SelectedMovie({ movie, latencyMs, onSelectMovie, onBack }) {
  const [media, setMedia] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    let alive = true;
    setMedia(null);
    if (movie) getMovieMedia(movie).then((m) => alive && setMedia(m));
    return () => { alive = false; };
  }, [movie?.movie_id]);

  if (!movie) return null;

  const genresList = movie.genres ? movie.genres.split('|') : [];
  const trailerUrl = media?.trailerKey
    ? `https://www.youtube.com/watch?v=${media.trailerKey}`
    : `https://www.youtube.com/results?search_query=${encodeURIComponent(movie.title + ' official trailer')}`;
  const hours = media?.runtime ? `${Math.floor(media.runtime / 60)}h ${media.runtime % 60}m` : null;

  return (
    <section className="selected-movie-hero" id="selected-movie-section">
      {media?.backdrop && (
        <div key={media.backdrop} className="hero-backdrop" style={{ backgroundImage: `url(${media.backdrop})` }} />
      )}
      <div className="hero-vignette"></div>

      <div className="hero-inner">
        <div className="hero-content">
          <div className="hero-topline">
            {onBack && (
              <button className="hero-back-btn" onClick={onBack} id="btn-new-search">← New search</button>
            )}
            <span className="selected-badge-tag">🎯 You searched for</span>
          </div>

          <h1 className="hero-title" id="selected-movie-title">{movie.title}</h1>

          <div className="hero-meta">
            <span className="hero-match" id="selected-movie-rating">★ {movie.avg_rating.toFixed(2)} / 5.0</span>
            {movie.release_year && <span>{movie.release_year}</span>}
            {hours && <span>{hours}</span>}
            <span>{movie.rating_count.toLocaleString()} ratings</span>
            {media?.tmdbRating ? <span className="hero-tmdb">TMDB {media.tmdbRating.toFixed(1)}</span> : null}
          </div>

          <div className="selected-genres">
            {genresList.map((g) => <span key={g} className="genre-pill">{g}</span>)}
          </div>

          {media?.overview && <p className="hero-overview">{media.overview}</p>}
          {media?.director && (
            <p className="hero-credits">
              <span>Director:</span> {media.director}
              {media.cast?.length > 0 && <> · <span>Starring:</span> {media.cast.slice(0, 3).join(', ')}</>}
            </p>
          )}

          <div className="hero-actions">
            <a className="btn-primary" href={trailerUrl} target="_blank" rel="noreferrer">▶ Watch Trailer</a>
            <button className="btn-secondary" onClick={() => setShowDetails(true)}>ⓘ More Info</button>
          </div>

          <div className="serving-debug-pill hero-debug-pill">
            <span>⚡ DuckDB serving tables · popularity {movie.popularity_score.toFixed(3)} · ID {movie.movie_id}</span>
            {latencyMs != null && <span>Serving latency: <strong>{latencyMs} ms</strong></span>}
          </div>
        </div>

        {media?.poster && <img key={media.poster} className="hero-poster" src={media.poster} alt={movie.title} />}
      </div>

      {showDetails && <MovieDetailsModal movie={movie} onClose={() => setShowDetails(false)} />}
    </section>
  );
}

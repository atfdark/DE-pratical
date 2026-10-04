import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { getMovieMedia } from '../services/tmdb';

export default function MovieDetailsModal({ movie, onClose, onSelect }) {
  const [d, setD] = useState(null);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    let alive = true;
    getMovieMedia(movie).then((x) => alive && setD(x));
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      alive = false;
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [movie.movie_id]);

  const genres = movie.genres ? movie.genres.split('|') : [];
  const hours = d?.runtime ? `${Math.floor(d.runtime / 60)}h ${d.runtime % 60}m` : null;
  const year = movie.release_year || (movie.title.match(/\((\d{4})\)\s*$/) || [])[1];

  return createPortal(
    <div className="details-backdrop" onClick={onClose}>
      <div className="details-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label={movie.title}>
        <button className="details-close" onClick={onClose} aria-label="Close">✕</button>

        <div className="details-media">
          {playing && d?.trailerKey ? (
            <iframe
              title="Trailer"
              src={`https://www.youtube.com/embed/${d.trailerKey}?autoplay=1`}
              allow="autoplay; encrypted-media; fullscreen"
              allowFullScreen
            />
          ) : (
            <>
              {d?.backdrop
                ? <img className="details-backdrop-img" src={d.backdrop} alt="" />
                : <div className={`details-backdrop-img ${d ? '' : 'shimmer'}`} />}
              <div className="details-media-fade" />
              <div className="details-media-bottom">
                <h2>{movie.title}</h2>
                <div className="hero-actions" style={{ margin: 0 }}>
                  {d?.trailerKey && (
                    <button className="btn-primary" onClick={() => setPlaying(true)}>▶ Play Trailer</button>
                  )}
                  {onSelect && (
                    <button className="btn-secondary" onClick={() => { onSelect(movie); onClose(); }}>
                      ✨ More Like This
                    </button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        <div className="details-body">
          <div className="details-left">
            <div className="hero-meta">
              <span className="hero-match">★ {movie.avg_rating ? movie.avg_rating.toFixed(2) : 'N/A'}</span>
              {year && <span>{year}</span>}
              {hours && <span>{hours}</span>}
              {movie.rating_count != null && <span>{movie.rating_count.toLocaleString()} ratings</span>}
              {d?.tmdbRating ? <span className="hero-tmdb">TMDB {d.tmdbRating.toFixed(1)}</span> : null}
            </div>
            {d?.tagline && <p className="details-tagline">“{d.tagline}”</p>}
            <h4 className="details-label">About</h4>
            <p className="details-overview">
              {d ? d.overview || 'No description available for this title.' : 'Loading…'}
            </p>
          </div>

          <div className="details-right">
            {d?.director && <p><span className="details-key">Director:</span> {d.director}</p>}
            {d?.cast?.length > 0 && <p><span className="details-key">Cast:</span> {d.cast.join(', ')}</p>}
            <p><span className="details-key">Genres:</span> {genres.join(', ')}</p>
            <p className="details-source">Artwork &amp; description: TMDB · Ratings: MovieLens 100K</p>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}

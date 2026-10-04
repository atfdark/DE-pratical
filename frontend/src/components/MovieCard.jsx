import React, { useState, useEffect } from 'react';
import { getMovieMedia } from '../services/tmdb';
import MovieDetailsModal from './MovieDetailsModal';

export default function MovieCard({ movie, onSelect }) {
  const [media, setMedia] = useState(null);
  const [imgFailed, setImgFailed] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    let alive = true;
    setImgFailed(false);
    getMovieMedia(movie).then((m) => alive && setMedia(m));
    return () => { alive = false; };
  }, [movie.movie_id]);

  const percentageMatch = movie.similarity_score !== undefined
    ? Math.round(movie.similarity_score * 100)
    : null;

  const showPoster = media?.poster && !imgFailed;

  return (
    <>
      {showDetails && (
        <MovieDetailsModal movie={movie} onClose={() => setShowDetails(false)} onSelect={onSelect} />
      )}
      <article
        className="movie-card"
        data-movie-id={movie.movie_id}
        onClick={() => onSelect(movie)}
        title={`See movies like ${movie.title}`}
      >
        <div className="card-image-container">
          {showPoster ? (
            <img
              src={media.poster}
              alt={movie.title}
              className="movie-poster"
              loading="lazy"
              onError={() => setImgFailed(true)}
            />
          ) : (
            <div className={`poster-placeholder ${media ? '' : 'shimmer'}`}>
              {media && <span>{movie.title}</span>}
            </div>
          )}

          {percentageMatch !== null && (
            <span className="similarity-badge card-corner-badge" title={`Cosine Similarity: ${movie.similarity_score}`}>
              {percentageMatch}% Match
            </span>
          )}
          {movie.rank !== undefined && percentageMatch === null && (
            <span className="rank-badge card-corner-badge">#{movie.rank}</span>
          )}

          <div className="card-image-overlay">
            <div className="card-overlay-actions">
              <button className="circle-btn circle-btn-primary card-btn" title="Show similar movies"
                onClick={(e) => { e.stopPropagation(); onSelect(movie); }}>▶</button>
              <button className="circle-btn" title="About this movie"
                onClick={(e) => { e.stopPropagation(); setShowDetails(true); }}>ⓘ</button>
            </div>
            {media?.overview && <p className="card-overlay-overview">{media.overview}</p>}
          </div>
        </div>

        <div className="card-content">
          <h3 className="card-title">{movie.title}</h3>
          <p className="card-genres">{(movie.genres || '').split('|').join(' • ')}</p>
          <div className="card-footer">
            <div className="card-rating">
              <span>★ {movie.avg_rating ? movie.avg_rating.toFixed(1) : 'N/A'}</span>
              {movie.rating_count !== undefined && (
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  ({movie.rating_count})
                </span>
              )}
            </div>
          </div>
        </div>
      </article>
    </>
  );
}

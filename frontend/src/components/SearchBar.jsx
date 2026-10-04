import React, { useState, useEffect, useRef } from 'react';
import { searchMovies } from '../services/api';
import { getMovieMedia } from '../services/tmdb';

function SearchThumb({ movie }) {
  const [src, setSrc] = useState(null);
  useEffect(() => {
    let alive = true;
    getMovieMedia(movie).then((m) => alive && setSrc(m.poster));
    return () => { alive = false; };
  }, [movie.movie_id]);
  return src
    ? <img className="dropdown-thumb" src={src} alt="" loading="lazy" />
    : <div className="dropdown-thumb shimmer" />;
}

export default function SearchBar({ onSelectMovie, selectedMovie }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const wrapperRef = useRef(null);

  // Quick preset suggestions from real MovieLens 100K catalog
  const presets = ['Star Wars', 'Toy Story', 'Terminator', 'Alien', 'Pulp Fiction'];

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        const data = await searchMovies(query);
        setResults(data.results || []);
        setIsOpen(true);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [query]);

  // Click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (movie) => {
    onSelectMovie(movie);
    setQuery('');
    setIsOpen(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && results.length > 0) {
      handleSelect(results[0]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  return (
    <div className="search-section" ref={wrapperRef}>
      <div className="search-bar-wrapper">
        <span className="search-icon">🔍</span>
        <input
          id="movie-search-input"
          type="text"
          className="search-input"
          placeholder="Search for a movie (e.g. Star Wars, Toy Story, Alien)..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setIsOpen(true)}
          autoComplete="off"
        />
        {loading && <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Searching...</span>}
        {query && (
          <button
            className="search-clear-btn"
            onClick={() => {
              setQuery('');
              setResults([]);
            }}
            title="Clear search"
          >
            ✕
          </button>
        )}
      </div>

      {/* Preset Chips */}
      <div className="search-quick-tags">
        <span>Try searching:</span>
        {presets.map((title) => (
          <button
            key={title}
            className="quick-tag"
            onClick={() => setQuery(title)}
          >
            {title}
          </button>
        ))}
      </div>

      {/* Autocomplete Dropdown */}
      {isOpen && (
        <div className="search-dropdown" id="search-dropdown">
          {results.length > 0 ? (
            results.map((movie) => (
              <div
                key={movie.movie_id}
                className="dropdown-item"
                onClick={() => handleSelect(movie)}
              >
                <SearchThumb movie={movie} />
                <div className="dropdown-text">
                  <div className="dropdown-title">{movie.title}</div>
                  <div className="dropdown-genres">{movie.genres}</div>
                </div>
                <div className="dropdown-meta">
                  <span className="dropdown-rating">★ {movie.avg_rating.toFixed(1)}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    ({movie.rating_count} votes)
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div style={{ padding: '1rem', color: 'var(--text-muted)', textAlign: 'center' }}>
              No movies found matching "{query}". Try a different title.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

import React from 'react';
import MovieCard from './MovieCard';

export default function PopularMovies({ popularMovies, onSelectMovie, title = 'Popular on MovieLens' }) {
  if (!popularMovies || popularMovies.length === 0) return null;

  return (
    <section className="popular-section row-section" id="popular-movies-section" aria-label="Popular Movies">
      <div className="section-header">
        <h2 className="section-title">
          <span>🔥 {title}</span>
          <span className="row-subtitle">Bayesian Weighted Popularity Ranking</span>
        </h2>
      </div>

      <div className="cards-grid">
        {popularMovies.map((movie) => (
          <MovieCard key={movie.movie_id} movie={movie} onSelect={onSelectMovie} />
        ))}
      </div>
    </section>
  );
}

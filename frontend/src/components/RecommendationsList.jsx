import React from 'react';
import MovieCard from './MovieCard';

export default function RecommendationsList({
  sourceTitle,
  category,
  recommendations,
  loading,
  latencyMs,
  isFallback,
  fallbackReason,
  onSelectMovie
}) {
  if (loading) {
    return (
      <div className="state-container">
        <div className="spinner"></div>
        <p>Querying DuckDB serving tables for recommendations...</p>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return null; // Return nothing instead of state-container to avoid double empty states
  }

  return (
    <section className="recommendations-section row-section" id="recommendations-container" aria-label="Movie Recommendations">
      <div className="section-header">
        <h2 className="section-title">
          <span>Because you searched <em className="row-source">{sourceTitle}</em></span>
          {category && <span style={{ marginLeft: '10px', opacity: 0.8 }}>({category})</span>}
          <span className="row-subtitle">Precomputed TF-IDF + Cosine Similarity</span>
        </h2>

        {latencyMs != null && (
          <span className="latency-badge" id="rec-latency-badge">
            Serving Latency: {latencyMs} ms
          </span>
        )}
      </div>

      {isFallback && (
        <div className="fallback-alert">
          <strong>⚠️ Fallback Notice:</strong> {fallbackReason}
        </div>
      )}

      <div className="cards-grid">
        {recommendations.map((movie) => (
          <MovieCard key={movie.movie_id} movie={movie} onSelect={onSelectMovie} />
        ))}
      </div>
    </section>
  );
}

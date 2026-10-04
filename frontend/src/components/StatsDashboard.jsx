import React from 'react';

export default function StatsDashboard({ stats, loading }) {
  if (loading || !stats) {
    return (
      <div className="stats-banner">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="kpi-card" style={{ opacity: 0.6 }}>
            <span className="kpi-label">Loading Metric...</span>
            <span className="kpi-value">---</span>
            <span className="kpi-subtext">Fetching from DuckDB</span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <section className="stats-banner" aria-label="Dataset Statistics">
      <div className="kpi-card">
        <span className="kpi-label">Total Catalog Movies</span>
        <span className="kpi-value" id="kpi-total-movies">
          {stats.total_movies.toLocaleString()}
        </span>
        <span className="kpi-subtext">Indexed in DuckDB serving table</span>
      </div>

      <div className="kpi-card">
        <span className="kpi-label">Total User Ratings</span>
        <span className="kpi-value" id="kpi-total-ratings">
          {stats.total_ratings.toLocaleString()}
        </span>
        <span className="kpi-subtext">Ingested & cleaned ratings</span>
      </div>

      <div className="kpi-card">
        <span className="kpi-label">Global Mean Rating</span>
        <span className="kpi-value" id="kpi-avg-rating" style={{ color: 'var(--accent-warning)' }}>
          ★ {stats.average_rating.toFixed(2)} / 5.0
        </span>
        <span className="kpi-subtext">Baseline Bayesian prior (C)</span>
      </div>

      <div className="kpi-card">
        <span className="kpi-label">Serving Engine</span>
        <span className="kpi-value" style={{ color: 'var(--accent-cyan)' }}>
          DuckDB
        </span>
        <span className="kpi-subtext">{stats.total_genres} distinct genres mapped</span>
      </div>
    </section>
  );
}

import React from 'react';

export default function AnalyticsCharts({ stats, onSelectMovie }) {
  if (!stats) return null;

  const { rating_distribution = [], genres = [], most_rated = [] } = stats;

  // Max count for rating distribution bar scaling
  const maxRatingCount = Math.max(...rating_distribution.map((r) => r.count), 1);
  const totalRatingDistCount = rating_distribution.reduce((acc, r) => acc + r.count, 0) || 1;

  // Max count for top genres
  const topGenres = genres.slice(0, 6);
  const maxGenreCount = Math.max(...topGenres.map((g) => g.count), 1);

  return (
    <section className="analytics-section" id="analytics-section" aria-label="Dataset Visualizations">
      <div className="section-header">
        <h2 className="section-title">
          <span>📊 Dataset Serving Analytics</span>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 400 }}>
            (Real-Time Aggregations from DuckDB)
          </span>
        </h2>
      </div>

      <div className="analytics-grid">
        {/* Rating Distribution Histogram */}
        <div className="chart-card">
          <h3>Rating Distribution (1 - 5 Stars)</h3>
          <div>
            {rating_distribution.map((item) => {
              const pct = ((item.count / totalRatingDistCount) * 100).toFixed(1);
              const barWidth = `${(item.count / maxRatingCount) * 100}%`;
              return (
                <div key={item.rating} className="bar-chart-row">
                  <div className="bar-chart-label">
                    {'★'.repeat(item.rating)} ({item.rating})
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: barWidth,
                        background:
                          item.rating >= 4
                            ? 'linear-gradient(to right, #10b981, #06b6d4)'
                            : item.rating === 3
                            ? 'linear-gradient(to right, #6366f1, #8b5cf6)'
                            : 'linear-gradient(to right, #f59e0b, #ef4444)'
                      }}
                    />
                  </div>
                  <div className="bar-chart-val">{pct}%</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Genres Breakdown */}
        <div className="chart-card">
          <h3>Top Genres by Catalog Count</h3>
          <div>
            {topGenres.map((g) => {
              const barWidth = `${(g.count / maxGenreCount) * 100}%`;
              return (
                <div key={g.genre} className="bar-chart-row">
                  <div className="bar-chart-label" title={g.genre}>
                    {g.genre}
                  </div>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: barWidth }} />
                  </div>
                  <div className="bar-chart-val">{g.count}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Most Rated Movies Leaderboard */}
        <div className="chart-card">
          <h3>Most Ingested Movies (Feedback Volume)</h3>
          <div className="leaderboard-list">
            {most_rated.slice(0, 5).map((m) => (
              <div
                key={m.movie_id}
                className="leaderboard-item"
                onClick={() => onSelectMovie(m)}
                title="Click to view recommendations"
              >
                <div>
                  <strong>#{m.rank} {m.title}</strong>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {m.genres}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: 'var(--accent-warning)', fontWeight: 600 }}>
                    ★ {m.avg_rating.toFixed(2)}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {m.rating_count} ratings
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

import React from 'react';

export default function Header({ isHealthy, latencyMs, onOpenArchitecture }) {
  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-icon">🎬</div>
        <div className="brand-text">
          <h1>Movie Recommendation System</h1>
          <span className="brand-badge">Data Serving Architecture • DuckDB + FastAPI</span>
        </div>
      </div>

      <div className="header-actions">
        <div className="status-pill" title="Serving Layer Health">
          <span className={`status-dot ${isHealthy ? '' : 'offline'}`}></span>
          <span>{isHealthy ? 'Serving Layer Active' : 'Connecting to API...'}</span>
          {latencyMs !== null && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--accent-success)' }}>
              ({latencyMs}ms)
            </span>
          )}
        </div>

        <button 
          id="btn-architecture"
          className="btn-architecture" 
          onClick={onOpenArchitecture}
          title="Explain Data Engineering Architecture"
        >
          <span>📐 Architecture & Concepts</span>
        </button>
      </div>
    </header>
  );
}

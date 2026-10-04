import React from 'react';

export default function ArchitectureModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Architecture: Serving Data for Analytics & ML</h2>
          <button className="modal-close-btn" onClick={onClose} title="Close modal">
            ✕
          </button>
        </div>

        <div className="architecture-diagram">
{`+----------------------------------------------------------------------------------+
|                          OFFLINE / BATCH DATA PROCESSING                         |
|                                                                                  |
|  [Raw MovieLens 100K]                                                            |
|       |                                                                          |
|       v                                                                          |
|  [Pipeline: Ingest & Clean]  --> Schema validation, deduplication, year extract  |
|       |                                                                          |
|       v                                                                          |
|  [Pipeline: Transform]       --> Bayesian popularity shrinkage, feature_text     |
|       |                                                                          |
|       v                                                                          |
|  [ML Recommendation Engine]  --> TF-IDF n-grams + pairwise Cosine Similarity     |
+----------------------------------------------------------------------------------+
                                        |
                   PRECOMPUTED TABLES (DuckDB & Parquet)
                                        |
+----------------------------------------------------------------------------------+
|                            ONLINE DATA SERVING LAYER                             |
|                                                                                  |
|  [DuckDB Analytical Store]   --> 'movies', 'ratings_summary', 'recommendations'  |
|       |                                                                          |
|       v                                                                          |
|  [FastAPI Data Serving API]  --> Sub-millisecond indexed SQL, Pydantic contracts |
|       |                                                                          |
|       v                                                                          |
|  [React Frontend / App]      --> Low-latency Data Product consumption UI         |
+----------------------------------------------------------------------------------+`}
        </div>

        <div className="architecture-concept-block">
          <h4>1. Why Separate Processing from Serving?</h4>
          <p>
            Computing TF-IDF matrices and pairwise cosine similarity across thousands of movies
            is computationally intensive ($O(N^2)$ similarity complexity). If the API computed
            recommendations on the fly for every user request, response times would spike to hundreds
            of milliseconds or seconds. Precomputing recommendations during offline batch processing
            and storing them in DuckDB serving tables enables sub-5ms low-latency serving.
          </p>
        </div>

        <div className="architecture-concept-block">
          <h4>2. Why DuckDB & Parquet?</h4>
          <p>
            DuckDB is an embedded columnar analytical engine designed for OLAP queries.
            Unlike traditional transactional databases (e.g. SQLite, PostgreSQL), DuckDB excels at
            vectorized columnar execution, analytical joins, and zero-copy Parquet integration,
            providing high query concurrency without requiring heavy external database servers.
          </p>
        </div>

        <div className="architecture-concept-block">
          <h4>3. What is a "Data Product"?</h4>
          <p>
            A Data Product packages transformed data, algorithms, and analytical logic behind a
            stable, discoverable, documented contract (FastAPI REST endpoints). Any consumer—whether
            this React frontend, a mobile app, or a BI dashboard—can query recommendations without
            needing access to raw CSV files or data cleaning logic.
          </p>
        </div>

        <div className="architecture-concept-block">
          <h4>4. Bayesian Shrinkage Popularity Formula</h4>
          <p>
            To prevent movies with only a single 5-star review from dominating recommendations,
            the pipeline calculates a Bayesian weighted average:
            <code style={{ display: 'block', margin: '0.4rem 0', color: 'var(--accent-warning)', fontFamily: 'var(--font-mono)' }}>
              W = (v / (v + m)) * R + (m / (v + m)) * C
            </code>
            where <em>v</em> is rating count, <em>m</em> is threshold (15 votes), <em>R</em> is movie average, and <em>C</em> is global mean rating (~3.53).
          </p>
        </div>

        <button
          className="card-btn"
          style={{ width: '100%', marginTop: '1rem', padding: '0.7rem' }}
          onClick={onClose}
        >
          Close Architecture Guide
        </button>
      </div>
    </div>
  );
}

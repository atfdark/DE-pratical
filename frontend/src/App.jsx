import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import StatsDashboard from './components/StatsDashboard';
import SearchBar from './components/SearchBar';
import SelectedMovie from './components/SelectedMovie';
import RecommendationsList from './components/RecommendationsList';
import PopularMovies from './components/PopularMovies';
import AnalyticsCharts from './components/AnalyticsCharts';
import ArchitectureModal from './components/ArchitectureModal';
import PosterWall from './components/PosterWall';

import {
  fetchHealth,
  fetchDatasetStats,
  fetchPopularMovies,
  fetchRecommendations
} from './services/api';

export default function App() {
  const [isHealthy, setIsHealthy] = useState(false);
  const [apiLatency, setApiLatency] = useState(null);
  const [stats, setStats] = useState(null);
  const [popularMovies, setPopularMovies] = useState([]);

  // No movie is pre-selected: the user searches first, then recommendations are served.
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [recommendationsIndian, setRecommendationsIndian] = useState([]);
  const [recommendationsEnglish, setRecommendationsEnglish] = useState([]);
  const [recLoading, setRecLoading] = useState(false);
  const [recLatency, setRecLatency] = useState(null);
  const [isFallback, setIsFallback] = useState(false);
  const [fallbackReason, setFallbackReason] = useState(null);

  const [isArchitectureOpen, setIsArchitectureOpen] = useState(false);
  const [error, setError] = useState(null);

  // Initialize data on mount
  useEffect(() => {
    async function initApp() {
      const t0 = performance.now();
      try {
        const health = await fetchHealth();
        setIsHealthy(health.status === 'healthy');
        setApiLatency(Math.round(performance.now() - t0));
      } catch (err) {
        console.error('Backend health check error:', err);
        setIsHealthy(false);
      }

      try {
        const [statsData, popularData] = await Promise.all([
          fetchDatasetStats(),
          fetchPopularMovies(18)
        ]);
        setStats(statsData);
        setPopularMovies(popularData.results || []);
      } catch (err) {
        console.error('Failed to load initial dataset:', err);
        setError('Could not connect to the Data Serving Layer. Ensure FastAPI backend is running on port 8080.');
      }
    }
    initApp();
  }, []);

  async function loadRecommendationsForMovie(movie) {
    if (!movie) return;
    setSelectedMovie(movie);
    setRecLoading(true);
    setError(null);

    try {
      // Fetch more so we have enough to split into two lists
      const data = await fetchRecommendations(movie.movie_id, 100);
      const allRecs = data.results || [];
      
      setRecommendationsIndian(allRecs.filter(m => m.movie_id >= 500000).slice(0, 15));
      setRecommendationsEnglish(allRecs.filter(m => m.movie_id < 500000).slice(0, 15));
      
      setRecLatency(data.processing_time_ms);
      setIsFallback(data.is_fallback || false);
      setFallbackReason(data.fallback_reason || null);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setRecommendationsIndian([]);
      setRecommendationsEnglish([]);
      setError(`Failed to retrieve recommendations for ${movie.title}.`);
    } finally {
      setRecLoading(false);
    }
  }

  const handleSelectMovie = (movie) => {
    loadRecommendationsForMovie(movie);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNewSearch = () => {
    setSelectedMovie(null);
    setRecommendationsIndian([]);
    setRecommendationsEnglish([]);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => document.getElementById('movie-search-input')?.focus(), 300);
  };

  const hasSelection = !!selectedMovie;

  return (
    <div className="app-container">
      <Header
        isHealthy={isHealthy}
        latencyMs={apiLatency}
        onOpenArchitecture={() => setIsArchitectureOpen(true)}
      />

      {error && (
        <div className="fallback-alert" style={{ background: 'rgba(239, 68, 68, 0.15)', borderColor: '#ef4444', color: '#fca5a5' }}>
          <strong>Connection Alert:</strong> {error}
        </div>
      )}

      {/* Step 1: Search (full landing hero before a movie is chosen, compact bar afterwards) */}
      <section className={`search-hero ${hasSelection ? 'compact' : ''}`} aria-label="Search movies">
        {!hasSelection && <PosterWall movies={popularMovies} />}
        <div className="search-hero-content">
          {!hasSelection && (
            <>
              <h1 className="landing-title">Find your next favourite movie.</h1>
              <p className="landing-subtitle">
                Search any title from the MovieLens catalog. Similar movies are served instantly
                from precomputed DuckDB serving tables.
              </p>
            </>
          )}
          <SearchBar onSelectMovie={handleSelectMovie} selectedMovie={selectedMovie} />
        </div>
      </section>

      {/* Step 2: Searched movie + its recommendations */}
      {hasSelection && (
        <>
          <SelectedMovie
            movie={selectedMovie}
            latencyMs={recLatency}
            onSelectMovie={handleSelectMovie}
            onBack={handleNewSearch}
          />
          <RecommendationsList
            sourceTitle={selectedMovie.title}
            category="Indian Cinema"
            recommendations={recommendationsIndian}
            loading={recLoading}
            latencyMs={recLatency}
            isFallback={isFallback}
            fallbackReason={fallbackReason}
            onSelectMovie={handleSelectMovie}
          />
          <RecommendationsList
            sourceTitle={selectedMovie.title}
            category="International Cinema"
            recommendations={recommendationsEnglish}
            loading={recLoading}
            latencyMs={null} // Don't show latency badge twice
            isFallback={false} // Don't show fallback alert twice
            fallbackReason={null}
            onSelectMovie={handleSelectMovie}
          />
        </>
      )}

      <PopularMovies
        popularMovies={popularMovies}
        onSelectMovie={handleSelectMovie}
        title={hasSelection ? 'Popular on MovieLens' : 'Not sure? Start with a popular movie'}
      />

      {/* Behind the scenes: data engineering metrics for the presentation */}
      <section className="de-section" aria-label="Data engineering insights">
        <h2 className="de-section-title">⚙️ Behind the Scenes — Data Serving Pipeline</h2>
        <StatsDashboard stats={stats} loading={!stats} />
        <AnalyticsCharts stats={stats} onSelectMovie={handleSelectMovie} />
      </section>

      <ArchitectureModal
        isOpen={isArchitectureOpen}
        onClose={() => setIsArchitectureOpen(false)}
      />
    </div>
  );
}

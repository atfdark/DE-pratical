/**
 * API Service Client
 * ------------------
 * Handles all HTTP communication between React UI and FastAPI Data Serving Layer.
 * Supports direct localhost:8080 calls and Vite proxy.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8080';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return await res.json();
}

export async function fetchDatasetStats() {
  const res = await fetch(`${API_BASE}/api/stats`);
  if (!res.ok) throw new Error(`Failed to load dataset stats: ${res.statusText}`);
  return await res.json();
}

export async function fetchPopularMovies(limit = 12) {
  const res = await fetch(`${API_BASE}/api/popular?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to load popular movies: ${res.statusText}`);
  return await res.json();
}

export async function searchMovies(query, limit = 15) {
  if (!query || !query.trim()) return { query, count: 0, results: [], execution_time_ms: 0 };
  const res = await fetch(`${API_BASE}/api/movies/search?q=${encodeURIComponent(query.trim())}&limit=${limit}`);
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
  return await res.json();
}

export async function fetchMovieDetails(movieId) {
  const res = await fetch(`${API_BASE}/api/movies/${movieId}`);
  if (!res.ok) throw new Error(`Movie details not found for ID ${movieId}`);
  return await res.json();
}

export async function fetchRecommendations(movieId, topK = 10) {
  const res = await fetch(`${API_BASE}/api/movies/${movieId}/recommendations?top_k=${topK}`);
  if (!res.ok) throw new Error(`Failed to fetch recommendations for movie ID ${movieId}`);
  return await res.json();
}

export async function fetchGenres() {
  const res = await fetch(`${API_BASE}/api/genres`);
  if (!res.ok) throw new Error(`Failed to load genres`);
  return await res.json();
}

import React, { useEffect, useState } from 'react';
import { getMovieMedia } from '../services/tmdb';

/** Decorative, dimmed wall of real posters (from popular MovieLens titles) behind the search hero. */
export default function PosterWall({ movies }) {
  const [posters, setPosters] = useState([]);

  useEffect(() => {
    let alive = true;
    const list = (movies || []).slice(0, 18);
    Promise.all(list.map((m) => getMovieMedia(m))).then((res) => {
      if (alive) setPosters(res.map((r) => r.poster).filter(Boolean));
    });
    return () => { alive = false; };
  }, [movies]);

  if (posters.length === 0) return <div className="poster-wall" aria-hidden="true" />;

  // Repeat to fill the wall
  const tiles = [...posters, ...posters, ...posters].slice(0, 36);
  return (
    <div className="poster-wall" aria-hidden="true">
      <div className="poster-wall-grid">
        {tiles.map((src, i) => (
          <img key={i} src={src} alt="" loading="lazy" style={{ animationDelay: `${(i % 12) * 60}ms` }} />
        ))}
      </div>
    </div>
  );
}

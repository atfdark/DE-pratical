import os
import csv
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
from backend.config import settings

TMDB_API_KEY = settings.TMDB_API_KEY
if not TMDB_API_KEY:
    print("ERROR: TMDB_API_KEY is not set.")
    exit(1)

# Paths
movies_csv = "data/raw/ml-latest-small/movies.csv"
ratings_csv = "data/raw/ml-latest-small/ratings.csv"

# Configure retries
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 500, 502, 503, 504 ])
session.mount('https://', HTTPAdapter(max_retries=retries))

# Fetch Genres
try:
    genre_url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_API_KEY}&language=en-US"
    r = session.get(genre_url, timeout=10)
    genre_map = {g['id']: g['name'] for g in r.json().get('genres', [])}
    print("Fetched genre map.")
except Exception as e:
    print(f"Failed to fetch genres: {e}")
    # Hardcode TMDB genres just in case
    genre_map = {28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"}

# Get existing titles
existing_titles = set()
if os.path.exists(movies_csv):
    with open(movies_csv, "r", encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                existing_titles.add(row[1])

movies_to_write = []
ratings_to_write = []

start_movie_id = 600000
user_id = 999
timestamp = int(time.time())

print("Fetching top 2000 Indian Pan-India movies from TMDB...")
for page in range(1, 101):
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_original_language=hi|te|ta|kn|ml&sort_by=popularity.desc&page={page}"
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"Failed on page {page}")
            break
        
        results = resp.json().get("results", [])
        if not results:
            break

        for movie in results:
            title = movie.get('title', '').replace(',', '')
            release_date = movie.get('release_date', '')
            year = release_date[:4] if release_date else ''
            full_title = f"{title} ({year})" if year else title
            
            if full_title in existing_titles:
                continue
            
            existing_titles.add(full_title)
            
            genre_ids = movie.get('genre_ids', [])
            genres = "|".join([genre_map.get(gid, "Unknown") for gid in genre_ids])
            if not genres:
                genres = "(no genres listed)"
                
            vote_avg = movie.get('vote_average', 5.0)
            rating_5_scale = max(0.5, min(5.0, round((vote_avg / 2) * 2) / 2))
            if rating_5_scale == 0:
                rating_5_scale = 3.0
                
            movie_id = start_movie_id
            start_movie_id += 1
            
            movies_to_write.append([movie_id, full_title, genres])
            
            for u in range(900, 910):
                noise = random.choice([-0.5, 0.0, 0.5])
                final_rating = max(0.5, min(5.0, rating_5_scale + noise))
                ratings_to_write.append([u, movie_id, final_rating, timestamp])
                
        if page % 10 == 0:
            print(f"Fetched {page} pages...")
            
    except Exception as e:
        print(f"Error on page {page}: {e}")
        time.sleep(2) # Wait a bit before continuing

print(f"Total movies fetched: {len(movies_to_write)}")

print("Appending to movies.csv...")
with open(movies_csv, "a", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(movies_to_write)

print("Appending to ratings.csv...")
with open(ratings_csv, "a", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(ratings_to_write)

print("Done appending data!")

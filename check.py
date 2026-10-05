import duckdb
con = duckdb.connect('data/serving/movies.duckdb')
res = con.execute("SELECT movie_id FROM movies WHERE title LIKE '%Kabhi Khushi%'").fetchall()
if res:
    print(con.execute(f"SELECT m.title, m.movie_id, r.similarity_score FROM recommendations r JOIN movies m ON r.recommended_movie_id = m.movie_id WHERE r.movie_id = {res[0][0]} ORDER BY r.similarity_score DESC LIMIT 40").fetchall())



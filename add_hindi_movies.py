import os

# Map of genres to index
genres = [
    "unknown", "Action", "Adventure", "Animation", "Children's", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
    "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western"
]

movies = [
    (1683, "3 Idiots (2009)", "25-Dec-2009", "http://us.imdb.com/title/tt1187043/", ["Comedy", "Drama"]),
    (1684, "Dangal (2016)", "23-Dec-2016", "http://us.imdb.com/title/tt5074352/", ["Action", "Drama"]),
    (1685, "Sholay (1975)", "15-Aug-1975", "http://us.imdb.com/title/tt0073707/", ["Action", "Adventure"]),
    (1686, "Lagaan: Once Upon a Time in India (2001)", "15-Jun-2001", "http://us.imdb.com/title/tt0169102/", ["Drama", "Musical"]),
    (1687, "PK (2014)", "19-Dec-2014", "http://us.imdb.com/title/tt2338151/", ["Comedy", "Drama", "Sci-Fi"])
]

u_item_path = "data/raw/ml-100k/u.item"
u_data_path = "data/raw/ml-100k/u.data"

# Add movies
with open(u_item_path, "a", encoding="latin-1") as f:
    for m in movies:
        flags = ["0"] * 19
        for g in m[4]:
            flags[genres.index(g)] = "1"
        line = f"{m[0]}|{m[1]}|{m[2]}||{m[3]}|{'|'.join(flags)}\n"
        f.write(line)

# Add ratings (50 users, ratings 5 to each movie so they become top rated and popular)
with open(u_data_path, "a", encoding="latin-1") as f:
    for m in movies:
        for user_id in range(1, 51):
            # user_id \t item_id \t rating \t timestamp
            f.write(f"{user_id}\t{m[0]}\t5\t881250949\n")

print("Added hindi movies and ratings.")

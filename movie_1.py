import sqlite3
import requests

def create_db():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        imdb_id TEXT UNIQUE,
        title TEXT,
        year INTEGER,
        type TEXT,
        poster_url TEXT,
        
        -- Custom user fields
        my_rating REAL,
        my_notes TEXT
    );
    """)

    conn.commit()
    conn.close()

create_db()

OMDB_API_KEY = "bb917723"

def search_movies(query):
    url = "http://www.omdbapi.com/"
    params = {
        "apikey": OMDB_API_KEY,
        "s": query
    }

    response = requests.get(url, params=params)
    data = response.json()
    
    # OMDb returns {"Response": "False", "Error": "..."} if no results
    if data.get("Response") == "False":
        return []
    
    return data.get("Search", [])


def save_movie_to_db(movie):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO movies (imdb_id, title, year, type, poster_url)
        VALUES (?, ?, ?, ?, ?)
    """, (
        movie.get("imdbID"),
        movie.get("Title"),
        movie.get("Year"),
        movie.get("Type"),
        movie.get("Poster") if movie.get("Poster") != "N/A" else None
    ))

    conn.commit()
    conn.close()


# Example usage
title_query = input("Search for a title: ")
results = search_movies(title_query)
for movie in results:
    save_movie_to_db(movie)

print("OMDb search results saved to database!")


def update_my_data(imdb_id, rating=None, notes=None):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE movies
        SET my_rating = ?, my_notes = ?
        WHERE imdb_id = ?
    """, (rating, notes, imdb_id))

    conn.commit()
    conn.close()

# Example: rate a movie and add personal notes
#    update_my_data("tt1375666", rating=9.7, notes="Amazing visuals & story!")


def get_all_movies():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()

    cursor.execute("SELECT imdb_id, title, year, my_rating, my_notes FROM movies")
    rows = cursor.fetchall()

    conn.close()
    return rows

print(get_all_movies())



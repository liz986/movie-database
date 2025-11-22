import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests

# -----------------------------------------------------------
# Database Setup
# -----------------------------------------------------------
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
        )
    """)

    conn.commit()
    conn.close()

create_db()

OMDB_API_KEY = "bb917723"

# -----------------------------------------------------------
# OMDb Search Function
# -----------------------------------------------------------
def search_movies(query):
    url = "http://www.omdbapi.com/"
    params = {"apikey": OMDB_API_KEY, "s": query}

    response = requests.get(url, params=params)
    data = response.json()

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


def get_all_movies():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT imdb_id, title, year, type, poster_url, my_rating, my_notes
        FROM movies
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

# -----------------------------------------------------------
# GUI App
# -----------------------------------------------------------
root = tk.Tk()
root.title("Movie Database Manager")
root.geometry("850x500")

tab_control = ttk.Notebook(root)

tab_search = ttk.Frame(tab_control)
tab_saved = ttk.Frame(tab_control)

tab_control.add(tab_search, text="Search Movies")
tab_control.add(tab_saved, text="Saved Movies")
tab_control.pack(expand=True, fill="both")

# -----------------------------------------------------------
# TAB 1: SEARCH MOVIES
# -----------------------------------------------------------

# Search input
search_frame = ttk.Frame(tab_search)
search_frame.pack(pady=10)

ttk.Label(search_frame, text="Search title: ").grid(row=0, column=0)
search_var = tk.StringVar()
search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
search_entry.grid(row=0, column=1, padx=5)

def perform_search():
    query = search_var.get().strip()
    if not query:
        return

    results = search_movies(query)

    for row in tree_search.get_children():
        tree_search.delete(row)

    for m in results:
        tree_search.insert("", "end", values=(
            m.get("imdbID"),
            m.get("Title"),
            m.get("Year"),
            m.get("Type"),
            m.get("Poster"),
        ))

ttk.Button(search_frame, text="Search", command=perform_search).grid(row=0, column=2)

# Search results table
tree_search = ttk.Treeview(
    tab_search,
    columns=("imdb", "title", "year", "type", "poster"),
    show="headings",
    height=12
)
for col in ("imdb", "title", "year", "type", "poster"):
    tree_search.heading(col, text=col.upper())
    tree_search.column(col, width=150)

tree_search.pack(expand=True, fill="both")

def save_selected_movie():
    selected = tree_search.selection()
    if not selected:
        messagebox.showwarning("No selection", "Please select a movie.")
        return

    values = tree_search.item(selected[0], "values")
    movie = {
        "imdbID": values[0],
        "Title": values[1],
        "Year": values[2],
        "Type": values[3],
        "Poster": values[4]
    }

    save_movie_to_db(movie)
    messagebox.showinfo("Saved", f"Saved: {movie['Title']}")

ttk.Button(tab_search, text="Save Selected Movie to Database", command=save_selected_movie).pack(pady=10)

# -----------------------------------------------------------
# TAB 2: SAVED MOVIES
# -----------------------------------------------------------

tree_saved = ttk.Treeview(
    tab_saved,
    columns=("imdb", "title", "year", "type", "poster", "rating", "notes"),
    show="headings",
)
for col in ("imdb", "title", "year", "type", "poster", "rating", "notes"):
    tree_saved.heading(col, text=col.upper())
    tree_saved.column(col, width=130)

tree_saved.pack(expand=True, fill="both")

def refresh_saved():
    for row in tree_saved.get_children():
        tree_saved.delete(row)

    for m in get_all_movies():
        tree_saved.insert("", "end", values=m)

ttk.Button(tab_saved, text="Refresh", command=refresh_saved).pack(pady=5)

def edit_selected_movie():
    selected = tree_saved.selection()
    if not selected:
        messagebox.showwarning("No selection", "Select a movie to edit.")
        return

    imdb_id, title, year, mtype, poster, rating, notes = tree_saved.item(selected[0], "values")

    new_rating = simpledialog.askfloat("Edit Rating", f"Enter rating for '{title}':", initialvalue=rating)
    new_notes = simpledialog.askstring("Edit Notes", f"Enter notes for '{title}':", initialvalue=notes)

    update_my_data(imdb_id, new_rating, new_notes)
    refresh_saved()

ttk.Button(tab_saved, text="Edit Rating / Notes", command=edit_selected_movie).pack(pady=5)

refresh_saved()

root.mainloop()

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import requests
import urllib.request
import io

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
            my_rating REAL,
            my_review TEXT,
            is_favorite INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

create_db()

OMDB_API_KEY = "bb917723"

# -----------------------------------------------------------
# OMDb + Database Functions
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
        INSERT OR IGNORE INTO movies
        (imdb_id, title, year, type, poster_url)
        VALUES (?, ?, ?, ?, ?)
    """, (
        movie["imdbID"],
        movie["Title"],
        movie["Year"],
        movie["Type"],
        movie["Poster"] if movie["Poster"] != "N/A" else None
    ))
    conn.commit()
    conn.close()

def update_my_data(imdb_id, rating, review):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE movies
        SET my_rating=?, my_review=?
        WHERE imdb_id=?
    """, (rating, review, imdb_id))
    conn.commit()
    conn.close()

def get_all_movies():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT imdb_id, title, year, type,
               poster_url, my_rating, my_review, is_favorite
        FROM movies
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# -----------------------------------------------------------
# Poster Loader
# -----------------------------------------------------------
poster_cache = None

def load_poster(url, label, max_size=(400, 600)):
    global poster_cache
    if not url:
        label.config(image="", text="No Image")
        return
    try:
        with urllib.request.urlopen(url) as u:
            raw = u.read()
        img = Image.open(io.BytesIO(raw))
        img.thumbnail(max_size, Image.LANCZOS)
        poster_cache = ImageTk.PhotoImage(img)
        label.config(image=poster_cache, text="")
    except:
        label.config(image="", text="No Image")

# -----------------------------------------------------------
# GUI Setup
# -----------------------------------------------------------
root = tk.Tk()
root.title("Movie Database Manager")
root.geometry("1200x700")

tabs = ttk.Notebook(root)
tab_search = ttk.Frame(tabs)
tab_saved = ttk.Frame(tabs)
tabs.add(tab_search, text="Search Movies")
tabs.add(tab_saved, text="Saved Movies")
tabs.pack(expand=True, fill="both")

# ================== SEARCH TAB ==================
search_results_cache = {}

top = ttk.Frame(tab_search)
top.pack(pady=10)

ttk.Label(top, text="Search movie:").grid(row=0, column=0)
search_var = tk.StringVar()
ttk.Entry(top, textvariable=search_var, width=40).grid(row=0, column=1, padx=5)

def perform_search():
    query = search_var.get().strip()
    if not query:
        return
    results = search_movies(query)
    search_results_cache.clear()
    for r in tree_search.get_children():
        tree_search.delete(r)
    for m in results:
        search_results_cache[m["imdbID"]] = m
        tree_search.insert("", "end",
            values=(m["imdbID"], m["Title"], m["Year"], m["Type"])
        )

ttk.Button(top, text="Search", command=perform_search).grid(row=0, column=2)

frame = ttk.Frame(tab_search)
frame.pack(fill="both", expand=True, padx=10)

tree_search = ttk.Treeview(
    frame,
    columns=("imdb","title","year","type"),
    show="headings",
    height=20
)
for col in ("imdb","title","year","type"):
    tree_search.heading(col, text=col.upper())
    tree_search.column(col, width=200)
tree_search.pack(side="left", fill="both", expand=True)

poster_label_search = ttk.Label(frame, text="No Image")
poster_label_search.pack(side="right", padx=10)

def on_search_select(event):
    sel = tree_search.selection()
    if not sel:
        return
    imdb_id = tree_search.item(sel[0], "values")[0]
    movie = search_results_cache.get(imdb_id)
    load_poster(movie["Poster"] if movie else None, poster_label_search)

tree_search.bind("<<TreeviewSelect>>", on_search_select)

def save_selected():
    sel = tree_search.selection()
    if not sel:
        return
    imdb_id = tree_search.item(sel[0], "values")[0]
    save_movie_to_db(search_results_cache[imdb_id])
    refresh_saved()
    messagebox.showinfo("Saved", "Movie saved!")

ttk.Button(tab_search, text="Save Selected Movie", command=save_selected).pack(pady=10)

# ================== SAVED TAB ==================
saved_frame = ttk.Frame(tab_saved)
saved_frame.pack(fill="both", expand=True, padx=10)

tree_saved = ttk.Treeview(
    saved_frame,
    columns=("imdb","title","year","type","rating","review","fav"),
    show="headings",
    height=20
)
for col in ("imdb","title","year","type","rating","review","fav"):
    tree_saved.heading(col, text=col.upper())
    tree_saved.column(col, width=160)

tree_saved.column("fav", width=80, anchor="center")
tree_saved.pack(side="left", fill="both", expand=True)

poster_label_saved = ttk.Label(saved_frame, text="No Image")
poster_label_saved.pack(side="right", padx=10)

def on_saved_select(event):
    sel = tree_saved.selection()
    if not sel:
        return
    imdb_id = tree_saved.item(sel[0], "values")[0]
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT poster_url FROM movies WHERE imdb_id=?", (imdb_id,))
    row = cursor.fetchone()
    conn.close()
    load_poster(row[0] if row else None, poster_label_saved)

tree_saved.bind("<<TreeviewSelect>>", on_saved_select)

def refresh_saved():
    for r in tree_saved.get_children():
        tree_saved.delete(r)
    for m in get_all_movies():
        fav = "⭐" if m[7] == 1 else ""
        tree_saved.insert("", "end",
            values=(m[0], m[1], m[2], m[3], m[5], m[6], fav)
        )

def edit_movie():
    sel = tree_saved.selection()
    if not sel:
        return
    imdb_id, title, _, _, rating, review, _ = tree_saved.item(sel[0], "values")
    new_rating = simpledialog.askfloat("Rating", "Enter rating:", initialvalue=rating)
    new_review = simpledialog.askstring("Review", "Enter review:", initialvalue=review)
    update_my_data(imdb_id, new_rating, new_review)
    refresh_saved()

def toggle_favorite():
    sel = tree_saved.selection()
    if not sel:
        return
    imdb_id = tree_saved.item(sel[0], "values")[0]
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE movies SET is_favorite = NOT is_favorite WHERE imdb_id=?",
        (imdb_id,)
    )
    conn.commit()
    conn.close()
    refresh_saved()

def show_favorites():
    for r in tree_saved.get_children():
        tree_saved.delete(r)
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT imdb_id, title, year, type,
               poster_url, my_rating, my_review, is_favorite
        FROM movies WHERE is_favorite=1
    """)
    rows = cursor.fetchall()
    conn.close()
    for m in rows:
        tree_saved.insert("", "end",
            values=(m[0], m[1], m[2], m[3], m[5], m[6], "⭐")
        )

def delete_movie():
    sel = tree_saved.selection()
    if not sel:
        return
    imdb_id = tree_saved.item(sel[0], "values")[0]
    if messagebox.askyesno("Delete", "Delete this movie?"):
        conn = sqlite3.connect("movies.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM movies WHERE imdb_id=?", (imdb_id,))
        conn.commit()
        conn.close()
        refresh_saved()

ttk.Button(tab_saved, text="Refresh", command=refresh_saved).pack(pady=3)
ttk.Button(tab_saved, text="Edit Rating / Review", command=edit_movie).pack(pady=3)
ttk.Button(tab_saved, text="⭐ Mark / Unmark Favorite", command=toggle_favorite).pack(pady=3)
ttk.Button(tab_saved, text="Show Favorites Only", command=show_favorites).pack(pady=3)
ttk.Button(tab_saved, text="Delete Movie", command=delete_movie).pack(pady=3)

refresh_saved()
root.mainloop()
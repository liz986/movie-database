import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
from PIL import Image, ImageTk
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
            my_review TEXT
        )
    """)
    conn.commit()
    conn.close()

create_db()

OMDB_API_KEY = "bb917723"

# -----------------------------------------------------------
# Database / OMDb Functions
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
        movie["imdbID"],
        movie["Title"],
        movie["Year"],
        movie["Type"],
        movie["Poster"] if movie["Poster"] != "N/A" else None
    ))
    conn.commit()
    conn.close()

def update_my_data(imdb_id, rating=None, review=None):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE movies
        SET my_rating = ?, my_review = ?
        WHERE imdb_id = ?
    """, (rating, review, imdb_id))
    conn.commit()
    conn.close()

def get_all_movies():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT imdb_id, title, year, type, poster_url, my_rating, my_review
        FROM movies
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# -----------------------------------------------------------
# Poster Functions
# -----------------------------------------------------------
poster_cache_search = None
poster_cache_saved = None

def load_poster(url, label, is_search=True, max_size=(400,600)):
    global poster_cache_search, poster_cache_saved
    if not url:
        label.config(image="", text="No Image")
        return
    try:
        with urllib.request.urlopen(url) as u:
            raw = u.read()
        img = Image.open(io.BytesIO(raw))
        img.thumbnail(max_size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        label.config(image=photo, text="")
        if is_search:
            poster_cache_search = photo
        else:
            poster_cache_saved = photo
    except:
        label.config(image="", text="No Image")

# -----------------------------------------------------------
# GUI App
# -----------------------------------------------------------
root = tk.Tk()
root.title("Movie Database Manager")
root.geometry("1200x700")

tab_control = ttk.Notebook(root)
tab_search = ttk.Frame(tab_control)
tab_saved = ttk.Frame(tab_control)
tab_control.add(tab_search, text="Search Movies")
tab_control.add(tab_saved, text="Saved Movies")
tab_control.pack(expand=True, fill="both")

# ------------------ SEARCH TAB ------------------

search_results_cache = {}

search_frame = ttk.Frame(tab_search)
search_frame.pack(pady=10, padx=10, fill="x")

ttk.Label(search_frame, text="Search title: ").grid(row=0, column=0)
search_var = tk.StringVar()
search_entry = ttk.Entry(search_frame, textvariable=search_var, width=50)
search_entry.grid(row=0, column=1, padx=5)

def perform_search():
    query = search_var.get().strip()
    if not query:
        return

    results = search_movies(query)

    search_results_cache.clear()
    for m in results:
        search_results_cache[m["imdbID"]] = m  

    for row in tree_search.get_children():
        tree_search.delete(row)
    for m in results:
        tree_search.insert("", "end", values=(m["imdbID"], m["Title"], m["Year"], m["Type"]))

ttk.Button(search_frame, text="Search", command=perform_search).grid(row=0, column=2, padx=5)

results_frame = tk.Frame(tab_search)
results_frame.pack(fill="both", expand=True, padx=10, pady=5)

tree_search = ttk.Treeview(results_frame, columns=("imdb","title","year","type"), show="headings", height=25)
for col in ("imdb","title","year","type"):
    tree_search.heading(col, text=col.upper())
    tree_search.column(col, width=200)
tree_search.pack(side="left", fill="both", expand=True)

scrollbar_search = ttk.Scrollbar(results_frame, orient="vertical", command=tree_search.yview)
tree_search.configure(yscroll=scrollbar_search.set)
scrollbar_search.pack(side="left", fill="y")

# Poster preview frame
poster_frame_search = tk.LabelFrame(results_frame, text="Poster Preview", width=400)
poster_frame_search.pack(side="right", fill="both", expand=True, padx=10)
poster_label_search = tk.Label(poster_frame_search, text="No Image")
poster_label_search.pack(expand=True)

def on_search_select(event):
    selected = tree_search.selection()
    if not selected:
        poster_label_search.config(image="", text="No Image")
        return

    imdb_id = tree_search.item(selected[0], "values")[0]

    movie = search_results_cache.get(imdb_id)
    url = movie["Poster"] if movie and movie["Poster"] != "N/A" else None

    w = max(200, poster_frame_search.winfo_width() - 20)
    h = max(300, poster_frame_search.winfo_height() - 20)

    load_poster(url, poster_label_search, is_search=True, max_size=(w, h))

tree_search.bind("<<TreeviewSelect>>", on_search_select)

def resize_search_poster(event):
    on_search_select(None)

poster_frame_search.bind("<Configure>", resize_search_poster)

def save_selected_movie():
    selected = tree_search.selection()
    if not selected:
        messagebox.showwarning("No selection", "Please select a movie.")
        return
    imdb_id = tree_search.item(selected[0], "values")[0]
    movie = search_results_cache.get(imdb_id)
    if movie:
        save_movie_to_db(movie)
        messagebox.showinfo("Saved", f"Saved: {movie['Title']}")
        refresh_saved()

ttk.Button(tab_search, text="Save Selected Movie to Database", command=save_selected_movie).pack(pady=10)

# ------------------ SAVED TAB ------------------

saved_frame = tk.Frame(tab_saved)
saved_frame.pack(fill="both", expand=True, padx=10, pady=5)

tree_saved = ttk.Treeview(saved_frame, columns=("imdb","title","year","type","rating","review"), show="headings", height=25)
for col in ("imdb","title","year","type","rating","review"):
    tree_saved.heading(col, text=col.upper())
    tree_saved.column(col, width=180)
tree_saved.pack(side="left", fill="both", expand=True)

scrollbar_saved = ttk.Scrollbar(saved_frame, orient="vertical", command=tree_saved.yview)
tree_saved.configure(yscroll=scrollbar_saved.set)
scrollbar_saved.pack(side="left", fill="y")

poster_frame_saved = tk.LabelFrame(saved_frame, text="Poster Preview", width=400)
poster_frame_saved.pack(side="right", fill="both", expand=True, padx=10)
poster_label_saved = tk.Label(poster_frame_saved, text="No Image")
poster_label_saved.pack(expand=True)

def on_saved_select(event):
    selected = tree_saved.selection()
    if not selected:
        poster_label_saved.config(image="", text="No Image")
        return
    imdb_id = tree_saved.item(selected[0], "values")[0]

    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT poster_url FROM movies WHERE imdb_id=?", (imdb_id,))
    row = cursor.fetchone()
    conn.close()

    url = row[0] if row else None

    w = max(200, poster_frame_saved.winfo_width() - 20)
    h = max(300, poster_frame_saved.winfo_height() - 20)

    load_poster(url, poster_label_saved, is_search=False, max_size=(w, h))

tree_saved.bind("<<TreeviewSelect>>", on_saved_select)

def resize_saved_poster(event):
    on_saved_select(None)

poster_frame_saved.bind("<Configure>", resize_saved_poster)

def refresh_saved():
    for row in tree_saved.get_children():
        tree_saved.delete(row)
    for m in get_all_movies():
        tree_saved.insert("", "end", values=(m[0], m[1], m[2], m[3], m[5], m[6]))

def edit_selected_movie():
    selected = tree_saved.selection()
    if not selected:
        messagebox.showwarning("No selection", "Select a movie to edit.")
        return
    imdb_id, title, year, mtype, rating, review = tree_saved.item(selected[0], "values")
    new_rating = simpledialog.askfloat("Edit Rating", f"Enter rating for '{title}':", initialvalue=rating)
    new_review = simpledialog.askstring("Edit review", f"Enter review for '{title}':", initialvalue=review)
    update_my_data(imdb_id, new_rating, new_review)
    refresh_saved()
    resize_saved_poster(None)

ttk.Button(tab_saved, text="Refresh", command=refresh_saved).pack(pady=5)
ttk.Button(tab_saved, text="Edit Rating / review", command=edit_selected_movie).pack(pady=5)

refresh_saved()
root.mainloop()
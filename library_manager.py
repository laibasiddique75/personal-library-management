import streamlit as st
import pandas as pd
import json
import time
import os
from datetime import datetime
import requests
import plotly.express as px
import plotly.graph_objects as go
from streamlit_lottie import st_lottie

st.set_page_config(
    page_title="Personal Library Management System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load Lottie animation
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# Load or save the library safely
def load_library():
    if os.path.exists("library.json"):
        try:
            with open("library.json", "r") as file:
                content = file.read().strip()
                if content:
                    st.session_state.library = json.loads(content)
                else:
                    st.session_state.library = []
        except json.JSONDecodeError:
            st.error("❌ Error: library.json is corrupted. Resetting the library.")
            st.session_state.library = []
            save_library()
    else:
        st.session_state.library = []

def save_library():
    with open("library.json", "w") as file:
        json.dump(st.session_state.library, file, indent=4)

# Add and remove book logic
def add_book(title, author, publication_year, genre, read_status):
    book = {
        "title": title,
        "author": author,
        "publication_year": publication_year,
        "genre": genre,
        "read_status": read_status,
        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state.library.append(book)
    save_library()
    st.success("✅ Book added successfully!")

def remove_book(index):
    del st.session_state.library[index]
    save_library()
    st.success("❌ Book removed successfully!")

# Search
def search_books(term, by):
    return [
        book for book in st.session_state.library
        if term.lower() in book[by].lower()
    ]

# Stats
def get_library_stats():
    total = len(st.session_state.library)
    read = sum(1 for b in st.session_state.library if b["read_status"])
    genres = {}
    authors = {}
    decades = {}

    for b in st.session_state.library:
        genres[b["genre"]] = genres.get(b["genre"], 0) + 1
        authors[b["author"]] = authors.get(b["author"], 0) + 1
        try:
            decade = (int(b["publication_year"]) // 10) * 10
            decades[decade] = decades.get(decade, 0) + 1
        except:
            continue

    return {
        "total": total,
        "read": read,
        "percent": round((read / total * 100) if total > 0 else 0, 1),
        "genres": genres,
        "authors": authors,
        "decades": decades,
    }

# Visualizations
def create_visualizations(stats):
    st.subheader("📊 Visual Insights")

    pie = go.Figure(data=[go.Pie(
        labels=["Read", "Unread"],
        values=[stats["read"], stats["total"] - stats["read"]],
        hole=0.4,
        marker_colors=["#10B981", "#F87171"]
    )])
    pie.update_layout(title="Read vs Unread Books", height=400)
    st.plotly_chart(pie, use_container_width=True)

    if stats["genres"]:
        df_genre = pd.DataFrame({"Genre": stats["genres"].keys(), "Count": stats["genres"].values()})
        bar = px.bar(df_genre, x="Genre", y="Count", color="Count", color_continuous_scale="Blues")
        bar.update_layout(title="Books by Genre", height=400)
        st.plotly_chart(bar, use_container_width=True)

    if stats["decades"]:
        df_decade = pd.DataFrame({
            "Decade": [f"{k}s" for k in stats["decades"].keys()],
            "Count": stats["decades"].values()
        })
        line = px.line(df_decade, x="Decade", y="Count", markers=True)
        line.update_layout(title="Books by Publication Decade", height=400)
        st.plotly_chart(line, use_container_width=True)

# Session initialization
if "library" not in st.session_state:
    st.session_state.library = []

if "current_view" not in st.session_state:
    st.session_state.current_view = "View Library"

# Load the library at app start
load_library()

# Sidebar navigation
st.sidebar.title("📚 Navigation")
nav = st.sidebar.radio("Go to", ["View Library", "Add Book", "Search Books", "Library Stats"])
st.session_state.current_view = nav

# Lottie animation
lottie_book = load_lottieurl("https://assets9.lottiefiles.com/temp/1f20_aKAfIn.json")
if lottie_book:
    st.sidebar.lottie(lottie_book, height=200)

st.title("📖 Personal Library Manager")

# Views
if nav == "Add Book":
    st.subheader("➕ Add a New Book")
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Title")
            author = st.text_input("Author")
            year = st.number_input("Year", min_value=1000, max_value=datetime.now().year, value=2023)
        with col2:
            genre = st.selectbox("Genre", ["Fiction", "Non-Fiction", "Science", "Tech", "Romance", "Fantasy", "Poetry", "Art", "History"])
            status = st.radio("Status", ["Read", "Unread"], horizontal=True)
        submit = st.form_submit_button("Add Book")
        if submit and title and author:
            add_book(title, author, year, genre, status == "Read")

elif nav == "View Library":
    st.subheader("📚 Your Library")
    if not st.session_state.library:
        st.info("Your library is empty.")
    else:
        for i, book in enumerate(st.session_state.library):
            with st.container():
                st.markdown(f"""
                    <div class='book-card'>
                        <h4>{book['title']}</h4>
                        <p><strong>Author:</strong> {book['author']}</p>
                        <p><strong>Year:</strong> {book['publication_year']}</p>
                        <p><strong>Genre:</strong> {book['genre']}</p>
                        <p><span style="background-color:{'#10B981' if book['read_status'] else '#F87171'}; color:white; padding:0.2rem 0.6rem; border-radius:1rem;">
                            {"Read" if book['read_status'] else "Unread"}
                        </span></p>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Remove", key=f"remove_{i}"):
                        remove_book(i)
                        st.rerun()
                with col2:
                    new_status = not book["read_status"]
                    label = "Mark as Read" if not book["read_status"] else "Mark as Unread"
                    if st.button(label, key=f"toggle_{i}"):
                        st.session_state.library[i]["read_status"] = new_status
                        save_library()
                        st.rerun()

elif nav == "Search Books":
    st.subheader("🔍 Search Books")
    by = st.selectbox("Search By", ["title", "author", "genre"])
    term = st.text_input("Enter search term")
    if st.button("Search") and term:
        results = search_books(term, by)
        st.markdown(f"### Found {len(results)} result(s)")
        for book in results:
            st.markdown(f"""
                <div class='book-card'>
                    <h4>{book['title']}</h4>
                    <p><strong>Author:</strong> {book['author']}</p>
                    <p><strong>Year:</strong> {book['publication_year']}</p>
                    <p><strong>Genre:</strong> {book['genre']}</p>
                    <p><span style="background-color:{'#10B981' if book['read_status'] else '#F87171'}; color:white; padding:0.2rem 0.6rem; border-radius:1rem;">
                        {"Read" if book['read_status'] else "Unread"}
                    </span></p>
            """, unsafe_allow_html=True)

elif nav == "Library Stats":
    st.subheader("📈 Library Statistics")
    if not st.session_state.library:
        st.info("Add some books to see statistics.")
    else:
        stats = get_library_stats()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Books", stats["total"])
        col2.metric("Read Books", stats["read"])
        col3.metric("Read %", f"{stats['percent']}%")
        create_visualizations(stats)
        if stats["authors"]:
            st.markdown("### 🏆 Top Authors")
            top_authors = dict(sorted(stats["authors"].items(), key=lambda x: x[1], reverse=True)[:5])
            for author, count in top_authors.items():
                st.write(f"**{author}** - {count} book{'s' if count > 1 else ''}")

st.markdown("<hr><center>© 2025 Laiba Siddique - Personal Library Manager</center>", unsafe_allow_html=True)



import ast
from datetime import datetime

import requests
import streamlit as st
from decouple import config

from db import get_user

API_URL = config("API_URL")
SAVED_BOOKS_URL = f"{API_URL}/user-books/"
BOOK_COVER_URL = "https://books.google.com/books/content?id={bookid}&printsec=frontcover&img=1&zoom=1&source=gbs_gdata"

st.title("📚 Saved Books")

if "page" not in st.session_state:
    st.session_state.page = "Search Books"

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Search Books", "Saved Books", "AI Recommendations"],
    index=["Search Books", "Saved Books", "AI Recommendations"].index(
        st.session_state.page
    ),
)

if page != st.session_state.page:
    st.session_state.page = page
    match page:
        case "Search Books":
            st.switch_page("app.py")
        case "Saved Books":
            st.switch_page("pages/saved_books.py")
        case "AI Recommendations":
            st.switch_page("pages/ai_recommendations.py")


def fetch_saved_books(user_id):
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.get(
        SAVED_BOOKS_URL, params={"user_id": user_id}, headers=headers
    )
    return response.json() if response.status_code == 200 else []


def format_published_date(date_str):
    if isinstance(date_str, str) and "T" in date_str:
        try:
            return datetime.fromisoformat(date_str).strftime("%Y-%m-%d")
        except ValueError:
            return date_str
    return date_str or "N/A"


def parse_authors(authors):
    if isinstance(authors, str):
        try:
            authors = ast.literal_eval(authors)
        except (ValueError, SyntaxError):
            pass
    return ", ".join(authors) if isinstance(authors, (list, set)) else authors


def fetch_recommendations(book_id):
    rec_url = f"{API_URL}/books/{book['id']}/recommendations"
    response = requests.get(rec_url)
    return response.json() if response.status_code == 200 else ""


def update_book_status(user_id, book_id, status, rating, notes):
    update_url = f"{API_URL}/user-books/{user_id}/{book_id}/"
    payload = {
        "status": status,
        "rating": rating if rating is not None else None,
        "notes": notes if notes else "",
    }
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.patch(update_url, json=payload, headers=headers)
    return response.status_code == 200


def display_book(book):
    if "update_success" in st.session_state:
        st.success(st.session_state["update_success"])
        del st.session_state["update_success"]

    cover_image_url = (
        BOOK_COVER_URL.format(bookid=book["bookid"]) if "bookid" in book else None
    )
    published_date = format_published_date(book.get("published_date"))
    authors = parse_authors(book["authors"])

    book_id = book["id"]

    # 🔹 Ensure session state is initialized before rendering widgets
    if f"status_{book_id}" not in st.session_state:
        st.session_state[f"status_{book_id}"] = book.get("status", "to_read")
    if f"rating_{book_id}" not in st.session_state:
        st.session_state[f"rating_{book_id}"] = book.get("rating", 0)
    if f"notes_{book_id}" not in st.session_state:
        st.session_state[f"notes_{book_id}"] = book.get("notes", "")

    with st.container():
        col1, col2 = st.columns([1, 3])

        with col1:
            if cover_image_url:
                st.image(cover_image_url, width=120)

        with col2:
            st.subheader(book["title"])
            st.write(f"**Authors:** {authors}")
            st.write(f"**Published Date:** {published_date}")

            col3, col4 = st.columns([1, 1])
            with col3:
                st.selectbox(
                    "📖 Status",
                    ["reading", "completed", "to_read"],
                    key=f"status_{book_id}",
                )
            with col4:
                st.slider(
                    "⭐ Rating",
                    min_value=1,
                    max_value=5,
                    value=book.get("rating", 0),
                    key=f"rating_{book_id}",
                )

            st.text_area(
                "📝 Notes", value=book.get("notes", ""), key=f"notes_{book_id}"
            )

            if st.button("Update", key=f"update_{book_id}"):
                user = get_user(st.session_state.username)
                update_url = f"{API_URL}/user-books/{user.id}/{book_id}/"
                payload = {
                    "status": st.session_state[f"status_{book_id}"],
                    "rating": st.session_state[f"rating_{book_id}"],
                    "notes": st.session_state[f"notes_{book_id}"],
                }
                headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
                response = requests.patch(update_url, json=payload, headers=headers)
                if response.ok:
                    st.success(f"✅ Book '{book['title']}' updated successfully!")
                else:
                    st.error("❌ Failed to update book.")

        with st.expander(f"🔍 AI Recommendations for '{book['title']}'"):
            if st.button("Generate AI Recommendations", key=f"btn_{book['id']}"):
                rec_url = f"{API_URL}/books/{book['id']}/recommendations"
                response = requests.get(rec_url)
                st.session_state[f"rec_{book['id']}"] = (
                    response.json() if response.ok else "error"
                )

            recommendations = st.session_state.get(f"rec_{book['id']}", [])
            if recommendations == "error":
                st.error("Failed to get AI recommendations.")
            elif recommendations:
                for rec in recommendations:
                    with st.container():
                        st.markdown(f"### 📕 {rec['title']}")
                        st.write(f"**Authors:** {', '.join(rec['authors'])}")
                        if rec.get("cover_image_url"):
                            st.image(rec["cover_image_url"], width=120)
            else:
                st.info("No recommendations available.")

        st.write("---")


if "username" not in st.session_state:
    st.error("You need to be logged in to view saved books")
    st.stop()

user = get_user(st.session_state.username)


saved_books = fetch_saved_books(user.id)

if saved_books:
    with st.expander("⚙️ Sort & Filter Options"):
        sort_option = st.selectbox(
            "Sort books by:", ["Date Added", "Title", "Author", "Published Date"]
        )
        search_query = st.text_input("🔍 Search by title or author").strip().lower()

    if search_query:
        saved_books = [
            book
            for book in saved_books
            if search_query in book["title"].lower()
            or search_query in parse_authors(book["authors"]).lower()
        ]

    sort_keys = {
        "Date Added": lambda x: x["created_at"],
        "Title": lambda x: x["title"].lower(),
        "Author": lambda x: parse_authors(x["authors"]).lower(),
        "Published Date": lambda x: x.get("published_date", ""),
    }

    if sort_option in sort_keys:
        saved_books.sort(
            key=sort_keys[sort_option],
            reverse=(sort_option == "Date Added", "Published Date"),
        )

    for book in saved_books:
        display_book(book)
else:
    st.error("Failed to load saved books")

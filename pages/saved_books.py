import ast
from datetime import datetime

import requests
import streamlit as st
from decouple import config

from db import get_user

API_URL = config("API_URL")
SAVED_BOOKS_URL = f"{API_URL}/books/"
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


def fetch_saved_books():
    response = requests.get(SAVED_BOOKS_URL)
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
    cover_image_url = (
        BOOK_COVER_URL.format(bookid=book["bookid"]) if "bookid" in book else None
    )
    published_date = format_published_date(book.get("published_date"))
    authors = parse_authors(book["authors"])

    with st.container():
        st.subheader(book["title"])
        if cover_image_url is not None:
            st.image(cover_image_url, width=150, caption=book["title"])

        st.write(f"**👨‍💻 Authors:** {authors}")
        st.write(f"**📅 Published Date:** {published_date}")

        current_status = book.get("status", "to_read")
        current_rating = book.get("rating", 0)
        current_notes = book.get("notes", "")

        status = st.selectbox(
            "📖 Reading Status",
            options=["reading", "completed", "to_read"],
            index=["reading", "completed", "to_read"].index(current_status),
            key=f"status_{book['id']}",
        )

        rating = st.slider(
            "⭐ Rating (1-5)",
            min_value=1,
            max_value=5,
            value=current_rating,
            key=f"rating_{book['id']}",
        )

        notes = st.text_area("📝 Notes", value=current_notes, key=f"notes_{book['id']}")

        # Submit button
        if st.button("Update", key=f"update_{book['id']}"):
            user = get_user(st.session_state.username)
            success = update_book_status(user.id, book["id"], status, rating, notes)
            if success:
                st.success("Book updated successfully!")
            else:
                st.error("Failed to update book.")

        rec_key = f"rec_{book['id']}"
        if rec_key not in st.session_state:
            st.session_state[rec_key] = None

        with st.expander(f"🔍 AI Recommendations similar to '{book['title']}'"):
            if st.button("Generate AI Recommendations", key=f"btn_{book['id']}"):
                recommendations = fetch_recommendations(book["id"])
                st.session_state[rec_key] = recommendations

            if rec_key in st.session_state and st.session_state[rec_key] is not None:
                if st.session_state[rec_key] == "error":
                    st.error("Failed to get AI recommendations.")
                elif st.session_state[rec_key]:
                    for rec in st.session_state[rec_key]:
                        with st.container():
                            st.markdown(f"### 📕 {rec['title']}")
                            st.write(f"**👨‍💻 Authors:** {', '.join(rec['authors'])}")
                            if rec.get("cover_image_url"):
                                st.image(
                                    rec["cover_image_url"],
                                    width=150,
                                    caption=rec["title"],
                                )
                else:
                    st.info("No AI recommendations available.")

        st.divider()


saved_books = fetch_saved_books()

if saved_books:
    with st.expander("⚙️ Sort & Filter Options"):
        sort_option = st.selectbox(
            "Sort books by:", ["Title", "Author", "Published Date"]
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
        "Title": lambda x: x["title"].lower(),
        "Author": lambda x: parse_authors(x["authors"]).lower(),
        "Published Date": lambda x: x.get("published_date", ""),
    }

    if sort_option in sort_keys:
        saved_books.sort(
            key=sort_keys[sort_option], reverse=(sort_option == "Published Date")
        )

    for book in saved_books:
        display_book(book)
else:
    st.error("Failed to load saved books")

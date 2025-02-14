import ast
from datetime import datetime

import requests
import streamlit as st

from config import settings
from db import get_user

API_URL = settings.API_URL
SAVED_BOOKS_URL = f"{API_URL}/user-books/"
GOOGLE_BOOKS_SEARCH_URL = f"{API_URL}/google-books/search/"
GOOGLE_BOOKS_DETAILS_URL = f"{API_URL}/google-books/details/"
BOOK_COVER_URL = "https://books.google.com/books/content?id={bookid}&printsec=frontcover&img=1&zoom=1&source=gbs_gdata"

st.title("📚 Saved Books")

# Ensure session state variables exist
st.session_state.setdefault("access_token", None)
st.session_state.setdefault("username", None)
st.session_state.setdefault("ai_recommendations", [])
st.session_state.setdefault("selected_book_id", None)
st.session_state.setdefault("selected_book_details", None)
st.session_state.setdefault("saved_book_id", None)
st.session_state.setdefault("save_clicked", False)
st.session_state.setdefault("page", "Saved Books")


if "page" not in st.session_state:
    st.session_state.page = "Search Books"

if st.session_state.access_token:
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.access_token = None
        st.session_state.username = None
        st.rerun()

st.sidebar.title("Navigation")
if st.session_state.access_token:
    pages = ["Search Books", "Saved Books", "AI Recommendations"]
else:
    pages = ["Login", "Search Books", "AI Recommendations"]

if "page" not in st.session_state or st.session_state.page not in pages:
    st.session_state.page = "Search Books"

page = st.sidebar.radio(
    "Go to",
    pages,
    index=pages.index(st.session_state.page),
)

if page != st.session_state.page:
    st.session_state.page = page

    if page == "Search Books":
        st.session_state.search_results = []
        st.session_state.last_search_query = ""

    match page:
        case "Search Books":
            st.switch_page("app.py")
        case "Saved Books":
            st.switch_page("pages/saved_books.py")
        case "AI Recommendations":
            st.switch_page("pages/ai_recommendations.py")
        case "Login":
            st.switch_page("pages/login.py")


if "username" not in st.session_state:
    st.error("You need to be logged in to view saved books")
    st.stop()


# Function to fetch and store book details in session state
def fetch_book_details(book_id):
    details_url = f"{GOOGLE_BOOKS_DETAILS_URL}{book_id}/"
    response = requests.get(details_url)

    if response.status_code == 200:
        st.session_state.selected_book_details = response.json()
    else:
        st.session_state.selected_book_details = None
        st.error("Failed to fetch book details.")


# Callback function to handle "View Details" button
def view_details(book_id):
    if st.session_state.selected_book_id == book_id:
        st.session_state.selected_book_id = None
        st.session_state.selected_book_details = None
    else:
        st.session_state.selected_book_id = book_id
        fetch_book_details(book_id)


# Callback function to save a book
def save_book(book_id):
    if not st.session_state.access_token:
        st.warning("You must be logged in to save books.")
        return

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    user = get_user(st.session_state.username)
    save_response = requests.post(
        f"{API_URL}/google-books/{book_id}/save",
        json={"user_id": user.id},
        headers=headers,
    )

    if save_response.ok:
        st.session_state[f"saved_{book_id}"] = True
    else:
        st.session_state[f"saved_{book_id}"] = False
        st.session_state[f"save_error_{book_id}"] = save_response.text


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

    st.session_state.setdefault(f"status_{book_id}", book.get("status", "to_read"))
    st.session_state.setdefault(
        f"rating_{book_id}", book.get("rating") if book.get("rating") is not None else 1
    )
    st.session_state.setdefault(f"notes_{book_id}", book.get("notes", ""))

    with st.container():
        col1, col2 = st.columns([1, 3])

        with col1:
            if cover_image_url:
                st.image(cover_image_url, width=120)

        with col2:
            st.subheader(book["title"])
            st.write(f"**Authors:** {authors}")
            st.write(f"**Published Date:** {published_date}")

            # 🔹 Add "View Details" button
            if st.button("View Description", key=f"description_{book['id']}"):
                if st.session_state.get(f"show_description_{book['id']}", False):
                    st.session_state[f"show_description_{book['id']}"] = False
                else:
                    st.session_state[f"show_description_{book['id']}"] = True

            if st.session_state.get(f"show_description_{book['id']}", False):
                description = book.get("description", "No description available.")
                st.write(f"**Description:** {description}")

        with st.expander("📖 More Details & Edit"):
            col3, col4 = st.columns([1, 1])
            with col3:
                status_options = ["reading", "completed", "to_read"]
                status_value = st.session_state[f"status_{book_id}"]
                status_index = (
                    status_options.index(status_value)
                    if status_value in status_options
                    else 2
                )  # Default to "to_read"
                st.selectbox(
                    "📖 Status",
                    status_options,
                    index=status_index,
                    key=f"status_{book_id}",
                )
            with col4:
                rating_value = st.session_state[f"rating_{book_id}"]
                if rating_value is None:
                    rating_value = 1
                st.slider(
                    "⭐ Rating",
                    min_value=1,
                    max_value=5,
                    value=rating_value,
                    key=f"rating_{book_id}",
                )

            st.text_area(
                "📝 Notes",
                value=st.session_state[f"notes_{book_id}"],
                key=f"notes_{book_id}",
            )

            col5, col6 = st.columns([1, 1])
            with col5:
                if st.button("Update", key=f"update_{book_id}"):
                    user = get_user(st.session_state.username)
                    update_url = f"{API_URL}/user-books/{user.id}/{book_id}/"
                    payload = {
                        "status": st.session_state[f"status_{book_id}"],
                        "rating": st.session_state[f"rating_{book_id}"],
                        "notes": st.session_state[f"notes_{book_id}"],
                    }
                    headers = {
                        "Authorization": f"Bearer {st.session_state.access_token}"
                    }
                    response = requests.patch(update_url, json=payload, headers=headers)
                    if response.ok:
                        st.success(f"✅ Book '{book['title']}' updated successfully!")
                        st.session_state.saved_books = fetch_saved_books(user.id)
                        st.rerun()
                    else:
                        st.error("❌ Failed to update book.")

                with col6:
                    if st.button("Delete Book", key=f"delete_{book_id}"):
                        delete_book(book_id)

        with st.expander(f"🔍 AI Recommendations for '{book['title']}'"):
            if st.button("Generate AI Recommendations", key=f"btn_{book['id']}"):
                rec_url = f"{API_URL}/books/{book['id']}/recommendations"
                response = requests.get(rec_url)
                if response.ok:
                    st.session_state[f"rec_{book['id']}"] = response.json()
                else:
                    st.session_state[f"rec_{book['id']}"] = "error"

            recommendations = st.session_state.get(f"rec_{book['id']}", None)

            if recommendations == "error":
                st.error("Failed to get AI recommendations.")
            elif recommendations is None:
                st.info("Click the button to generate recommendations")
            elif recommendations:
                for rec in recommendations:
                    with st.container():
                        st.markdown(f"### 📕 {rec['title']}")
                        st.write(f"**Authors:** {', '.join(rec['authors'])}")
                        if rec.get("cover_image_url"):
                            st.image(rec["cover_image_url"], width=120)

                        col1, col2 = st.columns([1, 1])

                        with col1:
                            if st.button(
                                "Show Details",
                                key=f"details_{rec['id']}",
                                on_click=view_details,
                                args=(rec["id"],),
                            ):
                                pass

                        with col2:
                            if st.button(
                                "Save Book",
                                key=f"save_{rec['id']}",
                                on_click=save_book,
                                args=(rec["id"],),
                            ):
                                pass

                        # Show details if toggled
                        if st.session_state.get("selected_book_id") == rec["id"]:
                            details = st.session_state.get("selected_book_details")
                            if details:
                                st.write(
                                    f"**Description:** {details.get('description', 'No description available')}"
                                )
                                st.write(
                                    f"**Publisher:** {details.get('publisher', 'Unknown')}"
                                )
                                st.write(
                                    f"**Published Date:** {details.get('published_date', 'Unknown')}"
                                )
                            else:
                                st.warning("No details available.")

            else:
                st.info("No recommendations available.")

        st.write("---")


def delete_book(book_id):
    if not st.session_state.access_token:
        st.warning("You must be logged in to delete books.")
        return

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    user = get_user(st.session_state.username)

    delete_response = requests.delete(
        f"{API_URL}/user-books/{user.id}/{book_id}/", headers=headers
    )

    if delete_response.status_code == 204:
        st.success(f"✅ Book '{book_id}' deleted successfully!")
        st.session_state.saved_books = fetch_saved_books(user.id)
        st.rerun()
    else:
        st.error("❌ Failed to delete book.")


if "username" not in st.session_state or not st.session_state.username:
    st.error("You need to be logged in to view saved books.")
    st.stop()

user = get_user(st.session_state.username)

if user is None:
    st.error("User not found. Please log in again.")
    st.stop()

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
        reverse_sort = sort_option in ["Date Added", "Published Date"]
        saved_books.sort(
            key=sort_keys[sort_option],
            reverse=reverse_sort,
        )

    for book in saved_books:
        display_book(book)
else:
    st.error("Failed to load saved books")

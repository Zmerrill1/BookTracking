import requests
import streamlit as st

from config import settings
from db import get_user

st.set_page_config(page_title="Book Tracker", layout="centered")

st.title("📚 ReadRadar")

API_URL = settings.API_URL
GOOGLE_BOOKS_SEARCH_URL = f"{API_URL}/google-books/search/"
GOOGLE_BOOKS_DETAILS_URL = f"{API_URL}/google-books/details/"

# Ensure session state variables exist
st.session_state.setdefault("access_token", None)
st.session_state.setdefault("username", None)
st.session_state.setdefault("saved_book_id", None)
st.session_state.setdefault("save_clicked", False)
st.session_state.setdefault("selected_book_id", None)
st.session_state.setdefault("selected_book_details", None)
st.session_state.setdefault("search_results", [])
st.session_state.setdefault("page", "Search Books")


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


# Search form
st.header("Search for Books")

if "last_search_query" not in st.session_state:
    st.session_state.last_search_query = ""

with st.form("search_form"):
    search_query = st.text_input("Enter book title, author, or keyword").strip()
    submitted = st.form_submit_button("Search")

if search_query and (
    submitted
    or search_query != st.session_state.last_search_query
    or st.button("Search")
):
    st.session_state.last_search_query = search_query
    with st.spinner("Searching for books..."):
        try:
            response = requests.get(
                GOOGLE_BOOKS_SEARCH_URL, params={"term": search_query}
            )
            if response.status_code == 200:
                st.session_state.search_results = response.json()
                st.session_state.selected_book_details = (
                    None  # Reset details when searching
                )
                st.session_state.selected_book_id = None  # Reset book selection
            else:
                st.error("Failed to fetch books. Please try again later.")
        except Exception as e:
            st.error(f"An error occurred: {e}")


if st.session_state.search_results:
    st.success(f"Found {len(st.session_state.search_results)} books:")

    for book in st.session_state.search_results:
        with st.container():
            col1, col2 = st.columns([1, 3])

            with col1:
                st.image(book["cover_image_url"], width=120, caption=book["title"])

            with col2:
                st.subheader(book["title"])
                st.write(f"**Authors:** {', '.join(book.get('authors', ['Unknown']))}")
                st.write(f"**Published Date:** {book.get('published_date', 'N/A')}")

            col3, col4 = st.columns([1, 1])
            with col3:
                details_button_key = f"details_{book['id']}"
                st.button(
                    "View Details",
                    key=details_button_key,
                    on_click=view_details,
                    args=(book["id"],),
                )

            with col4:
                button_key = f"save_{book['id']}"

                if st.session_state.access_token:
                    st.button(
                        "Save Book",
                        key=button_key,
                        on_click=save_book,
                        args=(book["id"],),
                    )
                else:
                    st.button(
                        "Save Book (Login Required)", key=button_key, disabled=True
                    )

            if st.session_state.get(f"saved_{book['id']}", None) is True:
                st.success("✅ Book saved successfully!")
            elif st.session_state.get(f"saved_{book['id']}", None) is False:
                error_message = st.session_state.get(
                    f"save_error_{book['id']}", "Unkown error."
                )
                st.error(f"❌ Failed to save book: {error_message}")

        if (
            st.session_state.selected_book_id == book["id"]
            and st.session_state.selected_book_details
        ):
            book_details = st.session_state.selected_book_details
            with st.expander(
                f"📖 More Details: {book_details['title']}", expanded=True
            ):
                st.write(f"**Title:** {book_details['title']}")
                if book_details.get("subtitle"):
                    st.write(f"**Subtitle:** {book_details['subtitle']}")
                st.write(
                    f"**Authors:** {', '.join(book_details.get('authors', ['Unknown']))}"
                )
                st.write(f"**Publisher:** {book_details.get('publisher', 'N/A')}")
                st.write(
                    f"**Published Date:** {book_details.get('published_date', 'N/A')}"
                )
                st.write(f"**Description:** {book_details.get('description', 'N/A')}")

        st.write("---")


st.write("\n")
st.markdown("Made using FastAPI and Streamlit.")

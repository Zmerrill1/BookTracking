import requests
import streamlit as st
from decouple import config


def load_css():
    """Loads the global CSS file into Streamlit."""
    try:
        with open("styles/global.css") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("styles/global.css not found. UI not fully styled.")


st.set_page_config(page_title="Book Tracker", layout="centered")
load_css()
st.title("📚 ReadRadar")

API_URL = config("API_URL")
GOOGLE_BOOKS_SEARCH_URL = f"{API_URL}/google-books/search/"
GOOGLE_BOOKS_DETAILS_URL = f"{API_URL}/google-books/details/"

# Simulated user_id (Replace this with actual authentication later)
USER_ID = 1


# Ensure session state variables exist
if "saved_book_id" not in st.session_state:
    st.session_state.saved_book_id = None
if "save_clicked" not in st.session_state:
    st.session_state.save_clicked = False
if "selected_book_id" not in st.session_state:
    st.session_state.selected_book_id = None
if "selected_book_details" not in st.session_state:
    st.session_state.selected_book_details = None
if "search_results" not in st.session_state:
    st.session_state.search_results = []
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
    if page == "Search Books":
        st.switch_page("app.py")
    elif page == "Saved Books":
        st.switch_page("pages/saved_books.py")
    elif page == "AI Recommendations":
        st.switch_page("pages/ai_recommendations.py")


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
    st.session_state.saved_book_id = book_id
    st.session_state.save_clicked = True
    st.rerun()  # Force full script rerun for saving


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
        st.image(book["cover_image_url"], width=150, caption=book["title"])
        st.subheader(book["title"])
        st.write(f"**Authors:** {', '.join(book.get('authors', ['Unknown']))}")
        st.write(f"**Published Date:** {book.get('published_date', 'N/A')}")

        col1, col2 = st.columns([1, 1])
        with col1:
            details_button_key = f"details_{book['id']}"
            st.button(
                "View Details",
                key=details_button_key,
                on_click=view_details,
                args=(book["id"],),
            )

        with col2:
            button_key = f"save_{book['id']}"
            st.button(
                "Save Book",
                key=button_key,
                on_click=save_book,
                args=(book["id"],),
            )

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


if st.session_state.save_clicked and st.session_state.saved_book_id:
    book_id = st.session_state.saved_book_id
    st.write(f"Debug: Sending save request for Book ID: {book_id}")

    save_response = requests.post(
        f"{API_URL}/google-books/{book_id}/save", json={"user_id": USER_ID}
    )

    if save_response.ok:
        st.success("Book saved successfully!")
    else:
        st.error(f"Failed to save book: {save_response.text}")

    st.session_state.saved_book_id = None
    st.session_state.save_clicked = False


st.write("\n")
st.markdown("Made using FastAPI and Streamlit.")

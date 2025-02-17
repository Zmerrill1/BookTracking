import requests
import streamlit as st

from config import settings

API_URL = settings.API_URL
RECOMMENDATIONS_URL = f"{API_URL}/recommend"
GOOGLE_BOOKS_DETAILS_URL = f"{API_URL}/google-books/details/"

st.title("📖 AI-Powered Book Recommendations")

# Ensure session state variables exist
st.session_state.setdefault("access_token", None)
st.session_state.setdefault("username", None)
st.session_state.setdefault("ai_recommendations", [])
st.session_state.setdefault("selected_book_id", None)
st.session_state.setdefault("selected_book_details", None)
st.session_state.setdefault("saved_book_id", None)
st.session_state.setdefault("save_clicked", False)
st.session_state.setdefault("page", "AI Recommendations")


def get_user_from_api():
    if not st.session_state.access_token:
        return None

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.get(f"{API_URL}/auth/users/me", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch user data: {response.text}")
        return None


if st.session_state.access_token:
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.access_token = None
        st.session_state.username = None
        st.rerun()


# Sidebar navigation
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


# Function to fetch AI recommendations (stored in session state)
def fetch_recommendations(query):
    response = requests.post(RECOMMENDATIONS_URL, json={"title": query})

    if response.status_code == 200:
        st.session_state.ai_recommendations = response.json()
    else:
        st.session_state.ai_recommendations = []
        st.error("Failed to fetch recommendations. Please try again.")


# Function to fetch book details using Google Books API (stored in session state)
def fetch_book_details(book_id):
    details_url = f"{GOOGLE_BOOKS_DETAILS_URL}{book_id}/"
    response = requests.get(details_url)

    if response.status_code == 200:
        st.session_state.selected_book_details = response.json()
    else:
        st.session_state.selected_book_details = None
        st.error("Failed to fetch book details.")


# Callback function to handle "View Details"
def view_details(book_id):
    if st.session_state.selected_book_id == book_id:
        st.session_state.selected_book_id = None
        st.session_state.selected_book_details = None
    else:
        st.session_state.selected_book_id = book_id
        fetch_book_details(book_id)


# Callback function to handle "Save" book
def save_book(book_id):
    if not st.session_state.access_token:
        st.warning("You must be logged in to save books.")
        return

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    user_id = st.session_state.user_id
    save_response = requests.post(
        f"{API_URL}/google-books/{book_id}/save",
        json={"user_id": user_id},
        headers=headers,
    )
    if save_response.ok:
        st.session_state[f"saved_{book_id}"] = True
    else:
        st.session_state[f"saved_{book_id}"] = False
        st.session_state[f"save_error_{book_id}"] = save_response.text


query_book_title = None

with st.form(key="search_form"):
    query_book_title = st.text_input("Enter a book title for recommendation:")
    submit_button = st.form_submit_button("Get Recommendations")

if submit_button:
    if not query_book_title.strip():
        st.warning("Please enter a book title before requesting recommendations.")
    else:
        fetch_recommendations(query_book_title)

# Display AI Recommendations
if st.session_state.ai_recommendations:
    st.success(f"Found {len(st.session_state.ai_recommendations)} recommended books:")

    for book in st.session_state.ai_recommendations:
        with st.container():
            col1, col2 = st.columns([1, 3])

            with col1:
                st.image(book["cover_image_url"], width=120)

            with col2:
                st.subheader(book["title"])
                st.write(f"**Authors:** {', '.join(book.get('authors', ['Unknown']))}")
                st.write(f"**Published Date:** {book.get('published_date', 'N/A')}")

                col3, col4 = st.columns([1, 1])
                with col3:
                    details_button_key = f"view_details_{book['id']}"
                    st.button(
                        "View Details",
                        key=details_button_key,
                        on_click=view_details,
                        args=(book["id"],),
                    )

                with col4:
                    save_button_key = f"save_{book['id']}"

                    if st.session_state.access_token:
                        st.button(
                            "Save",
                            key=save_button_key,
                            on_click=save_book,
                            args=(book["id"],),
                        )
                    else:
                        st.button(
                            "Save Book (Login Required)",
                            key=save_button_key,
                            disabled=True,
                        )

                if st.session_state.get(f"saved_{book['id']}", None) is True:
                    st.success("✅ Book saved successfully!")
                elif st.session_state.get(f"saved_{book['id']}", None) is False:
                    error_message = st.session_state.get(
                        f"save_error_{book['id']}", "Unknown Error"
                    )
                    st.error(f"❌ Failed to save book: {error_message}")

        # Expand book details if selected
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

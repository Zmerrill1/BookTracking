import requests
import streamlit as st

from config import settings

API_URL = settings.API_URL
RECOMMENDATIONS_URL = f"{API_URL}/recommend"
GOOGLE_BOOKS_DETAILS_URL = f"{API_URL}/google-books/details/"

st.title("📖 AI-Powered Book Recommendations")

# Ensure session state variables exist
st.session_state.setdefault("ai_recommendations", [])
st.session_state.setdefault("selected_book_id", None)
st.session_state.setdefault("selected_book_details", None)
st.session_state.setdefault("saved_book_id", None)
st.session_state.setdefault("save_clicked", False)
st.session_state.setdefault("page", "AI Recommendations")


# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Search Books", "Saved Books", "AI Recommendations"],
    index=["Search Books", "Saved Books", "AI Recommendations"].index(
        "AI Recommendations"
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

USER_ID = 1  # Replace with actual authentication when implemented


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
    st.session_state.saved_book_id = book_id
    st.session_state.save_clicked = True


query_book_title = None

with st.form(key="search_form"):
    query_book_title = st.text_input("Enter a book title for recommendation:")
    submit_button = st.form_submit_button("Get Recommendations")

if query_book_title and submit_button:
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
                    st.button(
                        "View Details",
                        key=f"details_{book['id']}",
                        on_click=view_details,
                        args=(book["id"],),
                    )

                with col4:
                    st.button(
                        "Save",
                        key=f"save_{book['id']}",
                        on_click=save_book,
                        args=(book["id"],),
                    )

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

# Show success message for saved book
if st.session_state.save_clicked and st.session_state.saved_book_id:
    book_id = st.session_state.saved_book_id

    save_response = requests.post(
        f"{API_URL}/google-books/{book_id}/save", json={"user_id": USER_ID}
    )

    if save_response.ok:
        st.success("✅ Book saved successfully!")
    else:
        st.error(f"❌ Failed to save book: {save_response.text}")

    st.session_state.saved_book_id = None
    st.session_state.save_clicked = False

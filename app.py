import requests
import streamlit as st
from decouple import config

st.set_page_config(page_title="Book Tracker", layout="centered")
st.title("📚 Book Tracker and Recommendations")


API_URL = config("API_URL")
GOOGLE_BOOKS_SEARCH_URL = f"{API_URL}/google-books/search/"

# Simulated user_id (Replace this with actual authentication later)
USER_ID = 1

# st.sidebar.title("Navigation")
# page = st.sidebar.radio("Go to", ["Search Books", "Saved Books", "AI Recommendations"])

# if page == "Saved Books":
#     st.switch_page("pages/saved_books.py")
# elif page == "AI Recommendations":
#     st.switch_page("pages/ai_recommendations.py")

# Ensure session state variables exist
if "saved_book_id" not in st.session_state:
    st.session_state.saved_book_id = None
if "save_clicked" not in st.session_state:
    st.session_state.save_clicked = False


# Define the callback function BEFORE using it
def save_book(book_id):
    st.session_state.saved_book_id = book_id
    st.session_state.save_clicked = True
    st.rerun()  # Force rerun so API call executes


# Search form
st.header("Search for Books")
search_query = st.text_input("Enter book title, author, or keyword")

if st.button("Search"):
    if search_query:
        with st.spinner("Searching for books..."):
            try:
                response = requests.get(
                    GOOGLE_BOOKS_SEARCH_URL, params={"term": search_query}
                )
                if response.status_code == 200:
                    books = response.json()
                    st.success(f"Found {len(books)} books:")

                    for book in books:
                        st.image(
                            book["cover_image_url"], width=150, caption=book["title"]
                        )
                        st.subheader(book["title"])
                        st.write(
                            f"**Authors:** {', '.join(book.get('authors', ['Unknown']))}"
                        )
                        st.write(
                            f"**Published Date:** {book.get('published_date', 'N/A')}"
                        )
                        st.write(f"[More Info]({book.get('info_link', '#')})")

                        # Create a unique key for each book
                        button_key = f"save_{book['id']}"

                        # Use callback function properly
                        st.button(
                            f"Save '{book['title']}'",
                            key=button_key,
                            on_click=save_book,
                            args=(book["id"],),  # Pass book ID to function
                        )

                        st.write("---")
                else:
                    st.error("Failed to fetch books. Please try again later.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a search query.")

# Process the save request after rerun
if st.session_state.save_clicked and st.session_state.saved_book_id:
    book_id = st.session_state.saved_book_id
    st.write(f"Debug: Sending save request for Book ID: {book_id}")

    save_response = requests.post(
        f"{API_URL}/google-books/{book_id}/save", json={"user_id": USER_ID}
    )

    st.write(f"Debug: Response Status Code: {save_response.status_code}")
    st.write(f"Debug: Response Text: {save_response.text}")

    if save_response.ok:
        st.success("Book saved successfully!")
    else:
        st.error(f"Failed to save book: {save_response.text}")

    # Reset session state
    st.session_state.saved_book_id = None
    st.session_state.save_clicked = False

# Footer
st.write("\n")
st.markdown("Made using FastAPI and Streamlit.")

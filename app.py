import streamlit as st
import requests

st.set_page_config(page_title="Book Tracker", layout="centered")
st.title("📚 Book Tracker and Recommendations")

#BACKEND API URL
API_URL = "http://127.0.0.1:8000/google-books/search/"

#Search form
st.header("Search for Books")
search_query = st.text_input("Enter book title or keyword")

if st.button("Search"):
    if search_query:
        with st.spinner("Searching for books..."):
            try:
                response = requests.get(API_URL, params={"term": search_query})
                if response.status_code == 200:
                    books = response.json()
                    st.success(f"Found {len(books)} books:")

                    for book in books:
                        st.subheader(book.get("title", "Unknown Title"))
                        st.write(f"**Authors:** {', '.join(book.get('authors', ['Unknown']))}")
                        st.write(f"**Published Date:** {book.get('published_date', 'N/A')}")
                        st.write(f"[More Info]({book.get('info_link', '#')})")
                        st.write("---")
                else:
                    st.error("Failed to fetch books. Please try again later.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a search query.")

# Footer
st.write("\n")
st.markdown("Made using FastAPI and Streamlit.")

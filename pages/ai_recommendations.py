import requests
import streamlit as st

from config import settings

API_URL = settings.API_URL
RECOMMENDATIONS_URL = f"{API_URL}/recommend"

st.title("📖 AI-Powered Book Recommendations")

USER_ID = 1  # Replace with actual authentication when implemented

query_book_title = st.text_input("Enter a book title for recommendation:")

if query_book_title:
    with st.spinner("Fetching AI recommendations..."):
        try:
            response = requests.post(
                RECOMMENDATIONS_URL, json={"title": query_book_title}
            )

            if response.status_code == 200:
                recommendations = response.json()
                st.success(f"Found {len(recommendations)} recommended books:")

                for book in recommendations:
                    st.image(book["cover_image_url"], width=150, caption=book["title"])
                    st.subheader(book["title"])
                    st.write(
                        f"**Authors:** {', '.join(book.get('authors', ['Unknown']))}"
                    )
                    st.write(f"**Published Date:** {book.get('published_date', 'N/A')}")
                    st.write(f"[More Info]({book.get('info_link', '#')})")
                    st.write("---")
            else:
                st.error("Failed to fetch recommendations. Please try again later.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

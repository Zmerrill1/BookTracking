import streamlit as st
import requests
from decouple import config

API_URL = config("API_URL")
SAVED_BOOKS_URL = f"{API_URL}/books/"

st.title("Saved Books")

response = requests.get(SAVED_BOOKS_URL)
if response.status_code == 200:
    saved_books = response.json()

    if saved_books:
        for book in saved_books:
            cover_image_url = book.get("cover_image")
            st.write(f"Cover Image URL: {cover_image_url}")
            if cover_image_url:
                st.image(cover_image_url, width=150, caption=book.get("title", "Unknown Title"))
            st.subheader(book["title"])
            st.write(f"**Authors:** {book['authors']}")
            st.write(f"**Published Date:** {book.get('published_date', 'N/A')}")

    else:
        st.write("No books saved yet.")
else:
    st.error("Failed to load saved books.")

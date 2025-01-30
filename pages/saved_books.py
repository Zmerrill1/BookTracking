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
            st.subheader(book["title"])
            st.write(f"**Authors:** {book['authors']}")
            st.write(f"**Authors:** {', '.join(book.get('authors', ['Unknown']))}")
            st.write(f"**Published Date:** {book.get('published_date', 'N/A')}")

    else:
        st.write("No books saved yet.")
else:
    st.error("Failed to load saved books.")

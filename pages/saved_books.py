import streamlit as st
import requests
from decouple import config

API_URL = config("API_URL")
SAVED_BOOKS_URL = f"{API_URL}/books/"
BOOK_COVER_URL = "https://books.google.com/books/content?id={bookid}&printsec=frontcover&img=1&zoom=1&source=gbs_gdata"

st.title("Saved Books")

response = requests.get(SAVED_BOOKS_URL)
if response.status_code == 200:
    saved_books = response.json()

    if saved_books:
        for book in saved_books:
            st.subheader(book["title"])
            if "bookid" in book and book["bookid"]:
                cover_image_url = BOOK_COVER_URL.format(bookid=book["bookid"])
            st.image(cover_image_url, width=150, caption=book["title"])
            st.write(f"**Authors:** {book['authors']}")
            st.write(f"**Published Date:** {book.get('published_date', 'N/A')}")

    else:
        st.write("No books saved yet.")
else:
    st.error("Failed to load saved books.")

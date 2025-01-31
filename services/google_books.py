import textwrap
from bs4 import BeautifulSoup
import httpx


BASE_URL = "https://www.googleapis.com/books/v1/volumes"
BOOK_URL = BASE_URL + "/{}"
SEARCH_URL = BASE_URL + "?q={}&langRestrict=en"

def search_books(term: str):
    """Search books by term"""

    query = SEARCH_URL.format(term)
    response = httpx.get(query)
    response.raise_for_status()

    books = []
    for item in response.json().get("items", []):
        google_id = item.get("id", "Unknown ID")
        volume_info = item.get("volumeInfo", {})
        title = volume_info.get("title", "Unknown Title")
        authors = volume_info.get("authors", ["Uknown Author"])
        published_date = volume_info.get("publishedDate", "Uknown Date")
        image_links = volume_info.get("imageLinks", {})
        cover_image = image_links.get("thumbnail")

        books.append({
            "google_id": google_id,
            "title": title,
            "authors": authors,
            "published_date": published_date,
            "cover_image": cover_image,
        })

    return books

def get_book_details(book_id: str):
    """Retrieve details for a specific book."""
    book_url = BOOK_URL.format(book_id)
    response = httpx.get(book_url)
    response.raise_for_status()
    return response.json().get("volumeInfo", {})

def clean_and_shorten_description(description: str, max_length: int = 300):
    """Remove HTML tags from the description and truncate it."""
    plain_text = BeautifulSoup(description, "html.parser").get_text()
    return textwrap.shorten(plain_text, width=max_length, placeholder="...")

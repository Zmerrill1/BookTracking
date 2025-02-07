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

    data = response.json()

    if "items" not in data or not data["items"]:
        return []

    books = []
    term_lower = term.lower()

    for item in data.get("items", []):
        google_id = item.get("id", "Unknown ID")
        volume_info = item.get("volumeInfo", {})
        title = volume_info.get("title", "Unknown Title")
        authors = volume_info.get("authors", ["Unknown Author"])
        published_date = volume_info.get("publishedDate", "Unknown Date")

        cover_image_url = volume_info.get("imageLinks", {}).get("thumbnail", "https://via.placeholder.com/150")

        title_lower = title.lower() if isinstance(title, str) else ""

        if not isinstance(authors, list):
            authors = []

        authors_lower = [author.lower() for author in authors if isinstance(author, str)]

        if isinstance(term_lower, str) and isinstance(title_lower, str):
            title_match = term_lower in title_lower
        else:
            title_match = False

        if isinstance(term_lower, str) and all(isinstance(author, str) for author in authors_lower):
            author_match = any(term_lower in author for author in authors_lower)
        else:
            author_match = False

        if not title_match and not author_match:
            continue


        books.append({
            "google_id": google_id,
            "title": title,
            "authors": authors,
            "published_date": published_date,
            "cover_image_url": cover_image_url,
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

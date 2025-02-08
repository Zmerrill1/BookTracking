from typing import List

import marvin

from config import settings
from models import BookSearchResult

marvin.settings.openai.api_key = settings.OPENAI_API_KEY


@marvin.fn
def recommend_similar_books(
    title: str, authors: List[str], description: str
) -> List[BookSearchResult]:
    """
    Given a book's title, authors, and description, return a list of similar books.
    The recommendations should consider similar books based on:
     - Similar genre
     - Related authors
     - Common themes or writing styles

     The output should return 3-5 similar books with titles, authors, and cover images.
    """

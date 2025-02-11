from typing import List

import marvin

from config import settings

marvin.settings.openai.api_key = settings.OPENAI_API_KEY


@marvin.fn
def recommend_similar_books(
    title: str, authors: List[str], description: str
) -> List[str]:
    """
    Given a book's title, authors, and description, return exactly **5 book titles** that are similar.

    Prioritize:
     - Books by the same author or in the same genre.
     - Well-known books with similar themes.
     - Critically acclaimed books.

     Return ** a Python list, not a single string, of exactly 5 book titles**, no more, no less.
    """

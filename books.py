import textwrap

from bs4 import BeautifulSoup
import httpx
import typer

app = typer.Typer()

BASE_URL = "https://www.googleapis.com/books/v1/volumes"
BOOK_URL = BASE_URL + "/{}"
SEARCH_URL = BASE_URL + "?q={}&langRestrict=en"


def search_books(term: str):
    """Search books by term."""
    query = SEARCH_URL.format(term)
    response = httpx.get(query)
    response.raise_for_status()

    books = []
    for item in response.json().get("items", []):
        try:
            google_id = item["id"]
            title = item["volumeInfo"]["title"]
            books.append((google_id, title))
        except KeyError:
            continue

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


@app.command()
def search(terms: list[str] = typer.Argument(..., help="Book search terms")):
    """Search for books and select one to view details."""
    search_string = " ".join(terms)
    books = search_books(search_string)

    if not books:
        typer.echo("No books found.")
        raise typer.Exit()

    typer.echo("Books found:")
    for idx, (book_id, title) in enumerate(books, start=1):
        typer.echo(f"{idx}. {title}")

    selection = typer.prompt(
        "Enter the number of the book you want details for", type=int
    )
    if selection < 1 or selection > len(books):
        typer.echo("Invalid selection.")
        raise typer.Exit()

    selected_book_id = books[selection - 1][0]
    typer.echo("Fetching details...")

    details = get_book_details(selected_book_id)

    typer.echo("\nBook Details:")
    typer.echo(f"Title: {details.get('title', 'N/A')}")
    typer.echo(f"Subtitle: {details.get('subtitle', 'N/A')}")
    typer.echo(f"Authors: {', '.join(details.get('authors', []))}")
    typer.echo(f"Publisher: {details.get('publisher', 'N/A')}")
    typer.echo(f"Published Date: {details.get('publishedDate', 'N/A')}")
    description = details.get("description", "N/A")
    typer.echo(f"Description: {clean_and_shorten_description(description)}")


if __name__ == "__main__":
    app()

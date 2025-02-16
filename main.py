from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc
from sqlmodel import Session, select

from auth import get_current_user
from auth import router as auth_router
from config import settings
from db import create_db_and_tables, get_session
from models import (
    Book,
    BookCreate,
    BookDetails,
    BookRead,
    BookSearchResult,
    SaveBookRequest,
    StatusEnum,
    User,
    UserBookResponse,
    UserBookStatus,
    UserBookStatusUpdate,
    UserRead,
)
from services.google_books import (
    clean_and_shorten_description,
    get_book_details,
    search_books,
)
from services.marvin_ai import recommend_similar_books

OPENAI_API_KEY = settings.OPENAI_API_KEY


@asynccontextmanager
async def lifespan(app):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_recommendations(
    title: str, authors: list[str] = [], description: str = ""
) -> list[BookSearchResult]:
    recommended_titles = recommend_similar_books(
        title=title, authors=authors, description=description
    )

    cleaned_titles = [title.split(" by ")[0] for title in recommended_titles]

    recommendations = []
    for title in cleaned_titles:
        google_books_results = search_books(title)

        if google_books_results:
            first_result = google_books_results[0]
            recommendations.append(
                BookSearchResult(
                    id=first_result["google_id"],
                    title=first_result["title"],
                    authors=first_result["authors"],
                    published_date=first_result["published_date"],
                    cover_image_url=first_result["cover_image_url"],
                )
            )

    return recommendations


def parse_published_date(date_str: str) -> Optional[datetime.date]:
    if not date_str or date_str == "N/A":
        return None

    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


@app.get("/")
def root():
    return {"message": "FastAPI is running!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.get("/users/", response_model=list[UserRead])
def get_users(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    users = session.exec(select(User)).all()
    return users


@app.post("/books/", response_model=BookRead)
def create_book(
    book: BookCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    db_book = Book(
        title=book.title,
        bookid=book.bookid,
        description=book.description,
        authors=book.authors,
        publisher=book.publisher,
        published_date=book.published_date,
    )
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book


@app.get("/books/", response_model=list[BookRead])
def get_books(session: Session = Depends(get_session)):
    books = session.exec(select(Book)).all()
    return [BookRead.model_validate(book, from_attributes=True) for book in books]


@app.post("/user-books/", response_model=UserBookStatus)
def add_user_book(
    user_book: UserBookStatus,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    db_user_book = UserBookStatus(**user_book.model_dump())
    session.add(db_user_book)
    session.commit()
    session.refresh(db_user_book)
    return db_user_book


@app.get("/user-books/", response_model=list[UserBookResponse])
def get_user_books(
    user_id: int,
    status: str = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    query = (
        select(UserBookStatus, Book)
        .join(Book, UserBookStatus.book_id == Book.id)
        .where(UserBookStatus.user_id == user_id)
        .order_by(desc(UserBookStatus.created_at))
    )

    if status:
        query = query.where(UserBookStatus.status == status)
    user_books = session.exec(query).all()

    if not user_books:
        raise HTTPException(status_code=404, detail="No saved books found.")

    books_with_details = [
        UserBookResponse(
            id=book.id,
            title=book.title,
            bookid=book.bookid,
            description=book.description,
            authors=book.authors,
            publisher=book.publisher,
            published_date=book.published_date,
            created_at=user_book_status.created_at,
            status=user_book_status.status,
            rating=user_book_status.rating,
            notes=user_book_status.notes,
        )
        for user_book_status, book in user_books
    ]
    return books_with_details


@app.patch("/user-books/{user_id}/{book_id}/", response_model=UserBookStatus)
def update_user_book(
    user_id: int,
    book_id: int,
    updates: UserBookStatusUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    db_user_book = session.exec(
        select(UserBookStatus)
        .where(UserBookStatus.user_id == user_id)
        .where(UserBookStatus.book_id == book_id)
    ).first()

    if db_user_book is None:
        raise HTTPException(status_code=404, detail="UserBookStatus not found.")

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_user_book, key, value)

    session.add(db_user_book)
    session.commit()
    session.refresh(db_user_book)
    return db_user_book


@app.delete("/user-books/{user_id}/{book_id}/", status_code=204)
def delete_user_book(
    user_id: int,
    book_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    db_user_book = session.exec(
        select(UserBookStatus)
        .where(UserBookStatus.user_id == user_id)
        .where(UserBookStatus.book_id == book_id)
    ).first()
    if db_user_book is None:
        raise HTTPException(status_code=404, detail="UserBookStatus not found.")
    session.delete(db_user_book)
    session.commit()
    return {"detail": "UserBookStatus deleted"}


@app.get("/google-books/search/", response_model=list[BookSearchResult])
def search_google_books(
    term: str = Query(
        ..., min_length=1, max_length=100, description="Search term for Google Books"
    ),
):
    books = search_books(term)

    if not books:
        raise HTTPException(
            status_code=404, detail=f"No books found for the search term '{term}'."
        )

    return [
        {
            "id": book["google_id"],
            "title": book["title"],
            "authors": book["authors"],
            "published_date": book["published_date"],
            "cover_image_url": book["cover_image_url"],
        }
        for book in books
    ]


@app.get("/google-books/details/{book_id}/", response_model=BookDetails)
def get_google_book_details(book_id: str):
    details = get_book_details(book_id)
    if not details:
        raise HTTPException(
            status_code=404, detail="Book with ID: '{book_id}' not found."
        )

    published_date = details.get("publishedDate", "N/A")

    if isinstance(published_date, str) and "T" in published_date:
        published_date = published_date.split("T")[0]

    return {
        "title": details.get("title", "N/A"),
        "bookid": book_id,
        "subtitle": details.get("subtitle", "N/A"),
        "authors": details.get("authors", []),
        "publisher": details.get("publisher", "N/A"),
        "published_date": published_date,
        "description": clean_and_shorten_description(details.get("description", "N/A")),
    }


@app.post("/google-books/{book_id}/save")
def save_google_book(
    book_id: str, request: SaveBookRequest, session: Session = Depends(get_session)
):
    user_id = request.user_id
    details = get_book_details(book_id)
    if not details:
        raise HTTPException(
            status_code=404, detail="Book with ID: '{book_id}' not found."
        )

    db_book = session.exec(
        select(Book).where(Book.title == details["title"])
    ).first()  # checking if the book exists in the db
    if db_book is None:
        db_book = Book(
            bookid=book_id,
            title=details.get("title", "N/A"),
            description=clean_and_shorten_description(details.get("description", "")),
            authors=", ".join(details.get("authors", [])),
            publisher=details.get("publisher", "N/A"),
            published_date=parse_published_date(details.get("publishedDate", "N/A")),
        )
        session.add(db_book)
        session.commit()
        session.refresh(db_book)

    db_user_book = session.exec(
        select(UserBookStatus).where(
            (UserBookStatus.user_id == user_id) & (UserBookStatus.book_id == db_book.id)
        )
    ).first()

    if db_user_book is None:
        user_book_status = UserBookStatus(
            user_id=user_id,
            book_id=db_book.id,
            status=StatusEnum.TO_READ,
        )
        session.add(user_book_status)
        session.commit()
        session.refresh(user_book_status)
        return user_book_status
    else:
        raise HTTPException(status_code=400, detail="Book is already saved by user.")


@app.get("/books/{book_id}/recommendations", response_model=list[BookSearchResult])
def get_book_recommendations(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    authors = book.authors.split(", ") if book.authors else []
    return get_recommendations(
        title=book.title, authors=authors, description=book.description or ""
    )


@app.post("/recommend", response_model=list[BookSearchResult])
def recommend_books(request: dict):
    title = request.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")

    return get_recommendations(title=title)

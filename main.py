from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Session, select
from passlib.context import CryptContext
from db import get_session, create_db_and_tables
from models import (
    Book,
    BookCreate,
    BookRead,
    User,
    UserBookStatus,
    UserBookStatusUpdate,
    UserCreate,
    UserRead,
    BookSearchResult,
    BookDetails,
    SaveBookRequest,
    StatusEnum
)
from services.google_books import (
    search_books,
    get_book_details,
    clean_and_shorten_description,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@asynccontextmanager
async def lifespan(app):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.get("/users/", response_model=list[UserRead])
def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users


@app.post("/books/", response_model=BookRead)
def create_book(book: BookCreate, session: Session = Depends(get_session)):
    db_book = Book(**book.model_dump())
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book


@app.get("/books/", response_model=list[BookRead])
def get_books(session: Session = Depends(get_session)):
    books = session.exec(select(Book)).all()
    return books


@app.post("/user-books/", response_model=UserBookStatus)
def add_user_book(
    user_book: UserBookStatus, session: Session = Depends(get_session)
):
    db_user_book = UserBookStatus(**user_book.model_dump())
    session.add(db_user_book)
    session.commit()
    session.refresh(db_user_book)
    return db_user_book


@app.get("/user-books/", response_model=list[UserBookStatus])
def get_user_books(
    user_id: int, status: str = None, session: Session = Depends(get_session)
):
    query = select(UserBookStatus).where(UserBookStatus.user_id == user_id)
    if status:
        query = query.where(UserBookStatus.status == status)
    user_books = session.exec(query).all()
    return user_books


@app.patch("/user-books/{user_id}/{book_id}/", response_model=UserBookStatus)
def update_user_book(
    user_id: int,
    book_id: int,
    updates: UserBookStatusUpdate,
    session: Session = Depends(get_session)
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
    session: Session = Depends(get_session)
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
    term: str = Query(..., min_length=1, max_length=100, description="Search term for Google Books")
):
    books = search_books(term)
    if not books:
        raise HTTPException(status_code=404, detail=f"No books found for the search term '{term}'.")
    return [
        {
            # TODO: with google id we can also make the cover image url here
            "id": book["google_id"],
            # TODO: can we remove google_id?
            "google_id": book["google_id"],
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
        raise HTTPException(status_code=404, detail="Book with ID: '{book_id}' not found.")
    return {
        "title": details.get("title", "N/A"),
        "subtitle": details.get("subtitle", "N/A"),
        "authors": details.get("authors", []),
        "publisher": details.get("publisher", "N/A"),
        "published_date": details.get("publishedDate", "N/A"),
        "description": clean_and_shorten_description(details.get("description", "N/A")),
    }


@app.post("/google-books/{book_id}/save")
def save_google_book(book_id: str, request: SaveBookRequest, session: Session = Depends(get_session)):
    user_id = request.user_id
    details = get_book_details(book_id)
    if not details:
        raise HTTPException(status_code=404, detail="Book with ID: '{book_id}' not found.")

    db_book=session.exec(select(Book).where(Book.title == details["title"])).first() #checking if the book exists in the db
    if db_book is None:
        db_book = Book(
            bookid = book_id,
            title=details.get("title", "N/A"),
            description=clean_and_shorten_description(details.get("description", "")),
            authors=details.get("authors", []),
            publisher=details.get("publisher", "N/A"),
            published_date=details.get("publishedDate", "N/A"),
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

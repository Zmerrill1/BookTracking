from contextlib import asynccontextmanager
from datetime import datetime

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select

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
    Token,
    User,
    UserBookStatus,
    UserBookStatusUpdate,
    UserCreate,
    UserRead,
)
from services.google_books import (
    clean_and_shorten_description,
    get_book_details,
    search_books,
)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


@asynccontextmanager
async def lifespan(app):
    create_db_and_tables()
    yield


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(lifespan=lifespan)


def get_current_user(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.pyJWTError:
        raise credentials_exception

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    return user


@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User(
        username=user.username,
        email=user.email,
    )
    db_user.set_password(user.password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.get("/users/", response_model=list[UserRead])
def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users


@app.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": user.get_token(), "token_type": "bearer"}


@app.get("/users/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/books/", response_model=BookRead)
def create_book(book: BookCreate, session: Session = Depends(get_session)):
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
def add_user_book(user_book: UserBookStatus, session: Session = Depends(get_session)):
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
    user_id: int, book_id: int, session: Session = Depends(get_session)
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
    print(f"DEBUG: search_books('{term}') returned: {books}")
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
            published_date=datetime.strptime(
                details.get("publishedDate", "N/A"), "%Y-%m-%d"
            ).date(),
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

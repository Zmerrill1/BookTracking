from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from typing import List
from models import Book, BookCreate, BookRead, Genre, GenreCreate, User, UserBookStatus, UserBookStatusCreate, UserBookStatusRead

app = FastAPI()

@app.post('/users/', response_model=User)
def create_user(user: User, session: Session = Depends(get_session)):
    db_user = User(**user.model_dump())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.get('/users/', response_model=List[User])
def get_users(session: Session= Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

@app.post('/books/', response_model=BookRead)
def create_book(book: BookCreate, session: Session = Depends(get_session)):
    genres = session.exec(select(Genre).where(Genre.id.in_(book.genres))).all()
    db_book = Book(**book.model_dump(exclude={"genres"}), genres=genres)
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book

@app.get('/books/', response_model=List[BookRead])
def get_books(session: Session = Depends(get_session)):
    books= session.exec(select(Book)).all()
    return books

@app.post('/genres/', response_model=Genre)
def create_genre(genre: GenreCreate, session: Session = Depends(get_session)):
    db_genre = Genre(**genre.model_dump())
    session.add(db_genre)
    session.commit()
    session.refresh(db_genre)
    return db_genre

@app.get('/genres/', response_model=List[Genre])
def get_genres(session: Session = Depends(get_session)):
    genres = session.exec(select(Genre)).all()
    return genres

@app.post('/user-books/', response_model=UserBookStatusRead)
def add_user_book(user_book: UserBookStatusCreate, session: Session = Depends(get_session)):
    db_user_book = UserBookStatus(**user_book.model_dump())
    session.add(db_user_book)
    session.commit()
    session.refresh(db_user_book)
    return db_user_book

@app.get('/user-books/', response_model=List[UserBookStatusRead])
def get_user_books(user_id: int, status: str = None, session: Session = Depends(get_session)):
    query = select(UserBookStatus).where(UserBookStatus.user_id == user_id)
    if status:
        query = query.where(UserBookStatus.status == status)
    user_books = session.exec(query).all()
    return user_books

@app.patch('/user-books/{id}/', response_model=UserBookStatusRead)
def update_user_book(id: int, updates: UserBookStatusCreate, session: Session = Depends(get_session)):
    db_user_book = session.get(UserBookStatus, id)
    if not db_user_book:
        raise HTTPException(status_code=404, detail="UserBookStatus not found.")
    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_user_book, key, value)
    session.add(db_user_book)
    session.commit()
    session.refresh(db_user_book)
    return db_user_book

@app.delete('/user-books/{id}/', response_model=dict)
def delete_user_book(id: int, session: Session = Depends(get_session)):
    db_user_book = session.get(UserBookStatus, id)
    if not db_user_book:
        raise HTTPException(status_code=404, detail="UserBookStatus not found.")
    session.delete(db_user_book)
    session.commit()
    return {"detail": "UserBookStatus deleted"}
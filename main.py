from fastapi import fastAPI, Depends
from sqlmodel import Session, select
from db import get_session
from models import Book, BookCreate, BookRead, Genre, GenreCreate

app = fastAPI()

@app.post('/books/', response_model=BookRead)
def create_book(book: BookCreate, session: Session = Depends(get_session)):
    db_book = Book.from_orm(book)
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book

@app.get('/books/', response_model=List[BookRead])
def get_books(session: Session = Depends(get_session)):
    books= session.exec(select(Book)).all()
    return books

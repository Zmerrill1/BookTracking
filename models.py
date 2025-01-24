from __future__ import annotations
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr
from typing import List
from datetime import datetime


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True, nullable=False)
    email: str | None = Field(unique=True, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    password_hash: str = Field(nullable=False)
    books: List["UserBookStatus"] = Relationship(back_populates='user')


#Many-to-Many relationship table.
class BookGenreLink(SQLModel, table=True):
    book_id: int | None = Field(default=None, foreign_key='book.id', primary_key=True)
    genre_id: int | None = Field(default=None, foreign_key='genre.id', primary_key=True)


class BookBase(SQLModel):
    title: str
    author: list[str] =[]
    description: str | None
    page_count: str | None
    rating: int | None = Field(default=None, ge=0, le=5)
    publisher: str | None
    published_date: datetime | None

class Book(BookBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    genres: List[Genre] = Relationship(back_populates='books', link_model=BookGenreLink)
    users: List['UserBookStatus'] = Relationship(back_populates='books')

class UserBookStatus(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id')
    book_id: int = Field(foreign_key='book.id')
    status: str = Field(nullable=False) # user determines, to_read, reading, or read
    rating: int | None = Field(default=None)
    notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None, nullable=True)

    user: User | None = Relationship(back_populates='books')
    book: Book | None = Relationship(back_populates='users')

class GenreBase(SQLModel):
    name: str

class Genre(GenreBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    books: List[Book] = Relationship(back_populates='genres', link_model=BookGenreLink)

#Pydantic models for API

class UserBookStatusCreate(SQLModel):
    book_id: int
    status: str
    rating: int | None
    notes: str | None

class UserBookStatusRead(SQLModel):
    id: int
    book: BookRead
    status: str
    rating: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        orm_mode = True
class BookCreate(BookBase):
    genres: List[int]

class BookRead(BookBase):
    id: int
    genres: List[GenreBase]
    class Config:
        orm_mode=True

class GenreCreate(GenreBase):
    pass

class GenreRead(GenreBase):
    id: int
    class Config:
        orm_mode=True

class UserCreate(UserBase):
    username: str
    email: EmailStr
    password: str #raw password

    class Config:
        orm_mode = True

class UserResponse(UserBase):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        orm_mode = True

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


#Many-to-Many relationship table. Genres can have many books, books can have many genres?
class BookGenreLink(SQLModel, table=True):
    book_id: Optional[int] = Field(default=None, foreign_key='book.id', primary_key=True)
    genre_id: Optional[int] = Field(default=None, foreign_key='genre.id', primary_key=True)


class BookBase(SQLModel):
    title: str
    author: str
    description: Optional[str] = None
    page_count: Optional[str] = None
    rating: Optional[float] = None
    published_date: Optional[datetime] = None

class Book(BookBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    genres: List[Genre] = Relationship(back_populates='books', link_model=BookGenreLink)

class GenreBase(SQLModel):
    name: str

class Genre(GenreBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    books: List[Book] = Relationship(back_populates='genres', link_model=BookGenreLink)

#Pydantic models for API
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
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime
from enum import Enum

class StatusEnum(str, Enum):
    READING = 'reading'
    COMPLETED = 'completed'
    TO_READ = 'to_read'

class UserBookStatus(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True, index=True)
    book_id: int = Field(foreign_key="book.id", primary_key=True, index=True)
    status: StatusEnum = Field(nullable=False, index=True)
    rating: Optional[int] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)


class UserBase(SQLModel):
    username: str
    email: Optional[str]


class User(UserBase, table=True):
    id: int = Field(default=None, primary_key=True)
    password_hash: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    books: List["Book"] = Relationship(
        back_populates="users", link_model=UserBookStatus
    )


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    created_at: datetime


class BookBase(SQLModel):
    title: str
    description: Optional[str]
    authors: Optional[str]
    publisher: Optional[str]
    published_date: Optional[datetime]


class Book(BookBase, table=True):
    id: int = Field(default=None, primary_key=True)
    users: List[User] = Relationship(
        back_populates="books", link_model=UserBookStatus
    )


class BookCreate(BookBase):
    pass


class BookRead(BookBase):
    id: int

class UserBookStatusUpdate(UserBookStatus):
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class BookSearchResult(SQLModel):
    id: str
    title: str

class BookDetails(SQLModel):
    title: str
    subtitle: str
    authors: list[str]
    publisher: str
    published_date: datetime
    description: str

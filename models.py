from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Optional

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, String
from sqlmodel import Field, Relationship, SQLModel

from config import settings

BOOK_COVER_URL = "https://books.google.com/books/content?id={bookid}&printsec=frontcover&img=1&zoom=1&source=gbs_gdata"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


class StatusEnum(str, Enum):
    READING = "reading"
    COMPLETED = "completed"
    TO_READ = "to_read"


class UserBase(SQLModel):
    username: str
    email: Optional[str]


class BookBase(SQLModel):
    title: str
    bookid: str
    description: Optional[str] = None
    authors: Optional[str] = Field(default=None, sa_column=Column(String))
    publisher: Optional[str] = None
    published_date: Optional[datetime] = None


class UserBookStatus(SQLModel, table=True):
    __tablename__ = "userbookstatus"
    __table_args__ = {"extend_existing": True}

    user_id: int = Field(foreign_key="user.id", primary_key=True, index=True)
    book_id: int = Field(foreign_key="book.id", primary_key=True, index=True)
    status: StatusEnum = Field(nullable=False, index=True)
    rating: Optional[int] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)


class User(UserBase, table=True):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    id: int = Field(default=None, primary_key=True)
    username: str = Field(nullable=False, unique=True)
    email: str = Field(nullable=False, unique=True)
    password_hash: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    def get_token(self) -> str:
        expire = datetime.now(UTC) + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode = {"sub": self.username, "exp": expire}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


class Book(BookBase, table=True):
    __tablename__ = "book"
    __table_args__ = {"extend_existing": True}

    id: int = Field(default=None, primary_key=True)
    bookid: str = Field(index=True, unique=True, nullable=False)


User.books = Relationship(back_populates="users", link_model=UserBookStatus)
Book.users = Relationship(back_populates="books", link_model=UserBookStatus)


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: str | None = None


class BookCreate(BookBase):
    pass


class BookRead(BookBase):
    id: int

    @property
    def cover_image_url(self) -> str:
        return BOOK_COVER_URL.format(bookid=self.bookid)

    class Config:
        from_attributes = True


class UserBookStatusUpdate(SQLModel):
    status: StatusEnum = Field(nullable=False, index=True)
    rating: Optional[int] = Field(default=None)
    notes: Optional[str] = Field(default=None)


class BookSearchResult(SQLModel):
    id: str
    title: str
    authors: list[str] = Field(default_factory=lambda: ["Unknown Author"])
    published_date: str = "Unknown Date"
    cover_image_url: str


class BookDetails(SQLModel):
    title: str
    bookid: str
    subtitle: str
    authors: list[str]
    publisher: str
    published_date: str
    description: str


class SaveBookRequest(BaseModel):
    user_id: int


class UserBookResponse(SQLModel):
    id: int
    title: str
    bookid: str
    description: Optional[str]
    authors: Optional[str]
    publisher: Optional[str]
    published_date: Optional[datetime]
    created_at: datetime
    status: str
    rating: Optional[int] = None
    notes: Optional[str] = None

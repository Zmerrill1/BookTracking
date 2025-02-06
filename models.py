from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum
from passlib.context import CryptContext
from config import settings
import jwt


BOOK_COVER_URL = "https://books.google.com/books/content?id={bookid}&printsec=frontcover&img=1&zoom=1&source=gbs_gdata"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

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

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    def get_token(self) -> str:
        expire = datetime.utcnow() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode = {
            "sub": self.username,
            "exp": expire
            }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


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


class BookBase(SQLModel):
    title: str
    bookid: str
    description: Optional[str] = None
    authors: Optional[str] = Field(default=None, sa_column=Column(String))
    publisher: Optional[str] = None
    published_date: Optional[datetime] = None


class Book(BookBase, table=True):
    id: int = Field(default=None, primary_key=True)
    bookid: str = Field(index=True, unique=True)

    users: List[User] = Relationship(
        back_populates="books", link_model=UserBookStatus
    )


class BookCreate(BookBase):
    pass


class BookRead(BookBase):
    id: int

    @property
    def cover_image_url(self) -> str:
        return BOOK_COVER_URL.format(bookid=self.bookid)

    class Config:
        from_attributes = True
class UserBookStatusUpdate(UserBookStatus):
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class BookSearchResult(SQLModel):
    id: str
    title: str
    authors: List[str] = Field(default_factory=lambda: ["Uknown Author"])
    published_date: str = "Uknown Date"
    cover_image_url: str

class BookDetails(SQLModel):
    title: str
    bookid: str
    subtitle: str
    authors: List[str]
    publisher: str
    published_date: datetime
    description: str

    # @property
    # def cover_image_url(self) -> str:
    #     return BOOK_COVER_URL.format(bookid=self.bookid)

class SaveBookRequest(BaseModel):
    user_id: int

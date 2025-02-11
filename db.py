from sqlmodel import Session, SQLModel, create_engine, select

from config import settings
from models import User

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_user(username) -> User | None:
    with Session(engine) as session:
        return session.exec(select(User).where(User.username == username)).first()

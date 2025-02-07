from sqlmodel import Session, SQLModel, create_engine

from config import settings

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

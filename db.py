from decouple import config
from sqlmodel import create_engine, Session, SQLModel

DATABASE_URL = config("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

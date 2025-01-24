import os

import dotenv
from sqlmodel import create_engine, Session, SQLModel

dotenv.load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

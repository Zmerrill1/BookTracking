import pytest
import bcrypt
from sqlmodel import SQLModel, create_engine, Session
from unittest.mock import patch
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from datetime import datetime

from main import app, get_session
from models import User, Book



# --------------------
# DB & CLIENT FIXTURES
# --------------------

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# --------------------
# USER FIXTURES
# --------------------
@pytest.fixture(name="create_test_user")
def create_test_user_fixture(session: Session):
    password = "password123"
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = User(username="validuser", email="valid@test.com", password_hash=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(name="user_token")
def user_token_fixture(client, create_test_user):
    response = client.post(
        "/token",
        data={"username": "validuser", "password": "password123"},
        headers={"Content-type": "application/x-www-form-urlencoded"}
    )
    return response.json()["access_token"]

# --------------------
# BOOK FIXTURES
# --------------------

@pytest.fixture(name="test_book")
def test_book_fixture(session: Session):
    book = Book(title="Test Book",
                bookid="abc123",
                authors=", ".join(["Author1", "Author2"]),
                publisher="Test Publisher",
                published_date=datetime(2024, 12, 31))
    session.add(book)
    session.commit()
    session.refresh(book)
    return book

# --------------------
# MOCK API CALL FIXTURES
# --------------------

@pytest.fixture
def mock_get_book_details():
    with patch("main.get_book_details") as mock:
        mock.return_value = {
            "title": "Test Book",
            "subtitle": "test subtitle",
            "description": "Testing books",
            "authors": ["Test Author"],
            "publisher": "Test Publisher",
            "publishedDate": "2024-12-31",
        }
        yield mock

@pytest.fixture
def mock_search_books():
    with patch("main.search_books") as mock:
        mock.return_value = [
            {
                "google_id": "12345",
                "title": "Python Book",
                "authors": ["Test Author"],
                "published_date": "2024-12-31",
                "cover_image_url": "https://via.placeholder.com/150"
            }
        ]
        yield mock

@pytest.fixture
def mock_get_book_details_not_found():
    with patch("main.get_book_details") as mock:
        mock.return_value = None
        yield mock

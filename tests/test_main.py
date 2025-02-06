import pytest
import bcrypt
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from datetime import datetime


from main import app, get_session
from models import User, Book


# --------------------
# DB & CLIENT FIXTURES
# --------------------

#notes for zach (will delete these later): pytest fixture to set up and teardown the test database for isolation
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

#pytest fixture to override 'get_session' from FastAPI in main.py with our test session. Clears that at the end.
@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="create_test_user")
def create_test_user_fixture(session: Session):
    password = "password123"
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = User(username="validuser", email="valid@test.com", password_hash=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

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

@pytest.fixture(name="user_token")
def user_token_fixture(client, create_test_user):
    response = client.post(
        "/token",
        data={"username": "validuser", "password": "password123"},
        headers={"Content-type": "application/x-www-form-urlencoded"}
    )
    return response.json()["access_token"]


# ------------------
# USER RELATED TESTS
# ------------------

def test_create_user(client):
    response = client.post('/users/', json={"username": "testuser", "email": "test@test.com", "password": "password123"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_get_users(client, create_test_user):
    response = client.get("/users/")
    assert response.status_code == 200
    users = response.json()

    assert isinstance(users, list)
    assert len(users) > 0

    expected_user = {
        "id": create_test_user.id,
        "username": create_test_user.username,
        "email": create_test_user.email
    }

    assert users[0]["id"] == expected_user["id"]
    assert users[0]["username"] == expected_user["username"]
    assert users[0]["email"] == expected_user["email"]

def test_read_users_me(client, user_token):
    response = client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "validuser"

def test_read_users_me_unauthenticated(client):
    response = client.get("/users/me")
    assert response.status_code == 401


# --------------------
# AUTHENTICATION TESTS
# --------------------

#testing authentication
@pytest.mark.parametrize(
    "username, password, expected_status, token_expected",
    [
        ("validuser", "password123", 200, True),
        ("invaliduser", "password123", 401, False),
        ("validuser", "wrongpassword", 401, False),
    ]
)
def test_login(client, create_test_user, username, password, expected_status, token_expected):
    """Test login functionality"""
    response = client.post(
        "/token",
        data={"username": username, "password": password},
        headers={"Content-type": "application/x-www-form-urlencoded"}
    )
    try:
        json_data = response.json()
    except ValueError:
        json_data = {}

    assert response.status_code == expected_status
    assert ("access_token" in json_data) == token_expected

# ------------------
# BOOK RELATED TESTS
# ------------------

def test_create_book(client):
    response = client.post("/books/", json={
        "title": "New Book",
        "bookid": "test123",
        "authors": "Author 1",
        "publisher": "Pub Test",
        "published_date": "2024-12-31"
    })
    assert response.status_code == 200
    assert response.json()["title"] == "New Book"

def test_get_books(client, test_book):
    response = client.get("/books/")
    assert response.status_code == 200
    assert any(book["title"] == "Test Book" for book in response.json())

#----------------------
#USER-BOOK STATUS TESTS
#----------------------

def test_add_user_book(client, create_test_user, test_book):
    response = client.post("/user-books/", json={"user_id": create_test_user.id, "book_id": test_book.id, "status": "to_read"})
    assert response.status_code == 200
    assert response.json()["status"] == "to_read"

def test_get_user_books(client, create_test_user, test_book):
    client.post("/user-books/", json={"user_id": create_test_user.id, "book_id": test_book.id, "status": "to_read"})
    response = client.get(f"/user-books/?user_id={create_test_user.id}")
    assert response.status_code == 200
    assert len(response.json()) > 0

#get the following error when running this one: TypeError: cannot pickle 'module' object
def test_update_user_book_status(client, create_test_user, test_book):
    client.post("/user-books/", json={"user_id": create_test_user.id, "book_id": test_book.id, "status": "to_read"})
    response = client.patch(f"/user-books/{create_test_user.id}/{test_book.id}/",
                            json={"status": "completed"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

def test_delete_user_book(client, create_test_user, test_book):
    client.post("/user-books/", json={"user_id": create_test_user.id, "book_id": test_book.id, "status": "to_read"})
    response = client.delete(f"/user-books/{create_test_user.id}/{test_book.id}/")
    assert response.status_code == 204

# ----------------------
# GOOGLE BOOKS API TESTS
# ----------------------

def test_search_google_books(client):
    response = client.get("/google-books/search/?term=Python")
    assert response.status_code in [200, 404]

def test_google_book_details(client):
    response = client.get("/google-books/details/RQ6xDwAAQBAJ/")
    print(f"DEBUG: {response.json()}")
    assert response.status_code in [200, 404]

def test_save_google_book(client, create_test_user):
    response = client.post("/google-books/details/RQ6xDwAAQBAJ/save", json={"user_id": create_test_user.id})
    assert response.status_code in [200, 400, 404]

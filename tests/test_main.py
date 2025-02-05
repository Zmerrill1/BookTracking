import pytest
import bcrypt
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from main import app, get_session
from models import User


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)


#notes for zach (will delete these later): pytest fixture to set up and teardown the test database for isolation
@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

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

    user = User(username="validuser", email="valid@test.com", password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_create_user(client):
    response = client.post('/users/', json={"username": "testuser", "email": "test@test.com", "password": "password123"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_get_users(client):
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


#testing authentication
@pytest.mark.parametrize(
    "username, password, expected_status",
    [
        ("validuser", "password123", 200),
        ("invaliduser", "password123", 401),
        ("validuser", "wrongpassword", 401),
    ]
)
def test_login(client, username, password, expected_status):
    """Test login functionality"""
    response = client.post(
        "/token",
        data={"username": username, "password": password},
        headers={"Content-type": "application/x-www-form-urlencoded"}
    )
    print(f"DEBUG: Response JSON -> {response.json()}")
    assert response.status_code == expected_status
    if response.status_code == 200:
        assert "access_token" in response.json()

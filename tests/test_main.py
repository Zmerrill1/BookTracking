import pytest
from bs4 import BeautifulSoup
import textwrap


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
    assert len(users) == 1

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
    assert len(response.json()) == 1

#get the following error when running this one: TypeError: cannot pickle 'module' object
def test_update_user_book_status(client, create_test_user, test_book):
    post_response = client.post("/user-books/", json={"user_id": create_test_user.id, "book_id": test_book.id, "status": "to_read"})
    assert post_response.status_code == 200

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

def test_search_google_books_success(client, mock_search_books):
    response = client.get("/google-books/search/?term=Python")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "12345",
            "title": "Python Book",
            "authors": ["Test Author"],
            "published_date": "2024-12-31",
            "cover_image_url": "https://via.placeholder.com/150"
        }
    ]

def test_search_google_books_not_found(client, mock_search_books):
    mock_search_books.return_value = []
    response = client.get("/google-books/search/?term=ajdflkajsdlfj")
    assert response.status_code == 404

def clean_and_shorten_description(description: str, max_length: int = 300):
    """Remove HTML tags from the description and truncate it."""
    plain_text = BeautifulSoup(description, "html.parser").get_text()
    return textwrap.shorten(plain_text, width=max_length, placeholder="...")

def test_google_book_details_success(client, mock_get_book_details):
    response = client.get("/google-books/details/RQ6xDwAAQBAJ/")

    expected_response = {
        "title": "Test Book",
        "bookid": "RQ6xDwAAQBAJ",
        "subtitle": "test subtitle",
        "authors": ["Test Author"],
        "publisher": "Test Publisher",
        "published_date": "2024-12-31",
        "description": clean_and_shorten_description("Testing books"),
    }

    assert response.status_code == 200
    assert response.json() == expected_response

def test_google_book_details_not_found(client, mock_get_book_details_not_found):
    response = client.get("/google-books/details/invalid-book-id/")
    assert response.status_code == 404

def test_save_google_book_success(client, create_test_user, mock_get_book_details):
    response = client.post("/google-books/RQ6xDwAAQBAJ/save", json={"user_id": create_test_user.id})
    assert response.status_code == 200
    assert response.json()["status"] == "to_read"

def test_save_google_book_invalid_data(client, create_test_user, mock_get_book_details):
    response = client.post("/google-books/RQ6xDwAAQBAJ/save", json={})
    assert response.status_code == 422

def test_save_google_book_not_found(client, create_test_user, mock_get_book_details_not_found):
    response = client.post("/google-books/InavlidID/save", json={"user_id": create_test_user.id})
    assert response.status_code == 404
    assert "Book with ID" in response.json()["detail"]

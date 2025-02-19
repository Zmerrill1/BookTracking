# 📚 Book Tracker & Recommendation App

This is a FastAPI + Streamlit project that allows users to search for books, track their reading, and receive AI-generated book recommendations.

## Live Demo

Checkout the live application on Streamlit: [ReadRadar](https://booktracking-huv5uj2rm5ec4rqgbf6tgn.streamlit.app)

## Table of Contents
1. [Features](#features)
2. [API Endpoints](#API-Endpoints)
3. [Installation & Setup](#Installation-&-Setup)
4. [Tech Stack](#Tech-Stack)
5. [Future Features](#future-features)
6. [License](#license)
7. [Acknowledgments](#acknowledgments)

## 🚀 Features

- **📖 Search Books**: Search for books using the Google Books API.
- **📚 Track Your Reads**: Save books to a personal reading list.
- **🤖 AI Recommendations**: Get book recommendations based on your interests.
- **📊 Interactive UI**: A user-friendly interface built with Streamlit.


## 📡 API Endpoints

### 🔍 Book Search  
#### GET /google-books/search?q={query}`  
Searches for books using the Google Books API.  

- **Query Params:** `term` (book title, author, or keyword)  
- **Response:** Returns a list of the top 10 or so matching books.  

---

### 📚 User Library  

#### POST /user-books/
Adds a book to the user's personal collection.  

- **Body:**  
  ```json
  {
    "title": "Book Name",
    "author": "Author",
  }
- Response: Returns the saved book details.

####  GET /user-books/
Retrieves all books in the user's saved collection.

#### DELETE /user-books/{user_id/{book_id}/
Removes a book from the collection.
Response: { "message": "Book deleted successfully" }


### 🤖 AI Recommendations

#### POST /recommendations/
Generates book recommendations based on a user's saved books.
-**Body:**
  ```json
  { "books": ["Book 1", "Book 2"] }
  ```
Response: A list of recommended books.

### 🤖 AI-Powered Book Recommendations

This app uses Marvin AI to generate personalized book recommendations.

How It Works:
1. The user saves books they’ve read or are interested in.
2. The backend sends this data to the AI recommendation system.
3. The AI suggests books based on themes, genres, and patterns.

Example Output:
  ```bash
  {
    "recommendations": [
      { "title": "The Hobbit", "author": "J.R.R. Tolkien" },
      { "title": "The Name of the Wind", "author": "Patrick Rothfuss" }
    ]
  }
  ```

## 🎯 Installation & Setup

1. Clone the Repository:
   ```bash
   git clone https://github.com/yourusername/book-tracker.git
   cd book-tracker
   ```
2. Set Up Backend (FastAPI):
  Ensure you have Python installed, then create a virtual environment:
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
  Install dependencies:
  ```bash
    uv pip install -r requirements.txt
    Set up environment variables:
  ```

  cp .env.example .env  Then edit with your API keys and DB settings
  
  Run database migrations:
  ```bash
  alembic upgrade head
  ```
  Start the FastAPI server:
  ```bash
    uvicorn app.main:app --reload
  ```
3. Set Up Frontend (Streamlit):
  Navigate to the frontend directory and install dependencies:
  ```bash
  cd frontend
  uv pip install -r requirements.txt
  ```
  Run the Streamlit app:
  ```bash
    streamlit run app.py
  ```

    
## 🛠️ Tech Stack
- Backend: [FastAPI](https://fastapi.tiangolo.com), [PostgreSQL](https://www.postgresql.org), [Alembic (for migrations)](https://pypi.org/project/alembic/)
- Frontend: [Streamlit](https://streamlit.io)
- External APIs: [Google Books API](https://developers.google.com/books), [Marvin AI (for recommendations)](https://www.askmarvin.ai)
- Deployment: [Fly.io (backend)](https://fly.io), [Streamlit Cloud (frontend)](https://streamlit.io/cloud)
  
To deploy updates:
- For backend:
  ```bash
  flyctl deploy
  ```
- For frontend if linked to Streamlit cloud:
  ```bash
  git push origin main
  ```
  
## 🔥 Future Features

- 📅 Reading progress tracking
- 🏆 Challenges & goals
- 📝 Contributing


## 📄 License

This project is licensed under the MIT License.

## Acknowledgements

- [PyBites PDM Program](https://pybit.es/catalogue/the-pdm-program/)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

---
Feel free to suggest any improvements or share your feedback by logging an issue against this repo!

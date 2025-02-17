Book Tracker & Recommendation App

Overview

This project is a Book Tracker & Recommendation App built with FastAPI and Streamlit. It allows users to search for books using the Google Books API, save books to their personal library, and receive AI-based book recommendations via Marvin AI.

Features

📚 Search Books - Find books using the Google Books API.

💾 Save Books - Add books to a personal reading list.

🤖 AI-Powered Recommendations - Get book recommendations based on search results and saved books.

🏗 Modern Stack - FastAPI for the backend, PostgreSQL for the database, and Streamlit for the frontend.

🚀 Deployed - FastAPI backend is deployed on Fly.io, and Streamlit frontend is hosted on Streamlit Cloud.

Tech Stack

Backend: FastAPI, PostgreSQL, Alembic (migrations)

Frontend: Streamlit

Database: PostgreSQL

AI Integration: Marvin AI for book recommendations

Deployment: FastAPI on Fly.io, Streamlit on Streamlit Cloud

Installation

1. Clone the repository

git clone https://github.com/yourusername/book-tracker.git
cd book-tracker

2. Set up the backend

Install dependencies

uv venv
source .venv/bin/activate  # (or `venv\Scripts\activate` on Windows)
uv pip install -r requirements.txt

Set up environment variables

Create a .env file and add the necessary environment variables:

DATABASE_URL=postgresql://user:password@localhost:5432/book_tracker
GOOGLE_BOOKS_API_KEY=your_google_books_api_key
MARVIN_API_KEY=your_marvin_api_key

Run database migrations

alembic upgrade head

Start the FastAPI server

uvicorn app.main:app --reload

The backend will be available at http://127.0.0.1:8000.

3. Set up the frontend

Install Streamlit dependencies

cd frontend
pip install -r requirements.txt

Run the Streamlit app

streamlit run app.py

The frontend will be available at http://localhost:8501.

Usage

Search for books using keywords.

View book details and save books to your personal library.

Get AI-powered recommendations based on your saved books.

Explore your reading list and discover new books.

API Endpoints

Method

Endpoint

Description

GET

/google-books/search?query=book_title

Search for books using Google Books API

POST

/books/

Save a book to the database

GET

/books/

Retrieve saved books

POST

/recommendations/

Get AI-based book recommendations

Deployment

The project is deployed using:

FastAPI Backend → Fly.io

Streamlit Frontend → Streamlit Cloud

Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

License

This project is licensed under the MIT License.

Contact

For any questions or suggestions, feel free to reach out:

GitHub: yourusername

Email: your.email@example.com


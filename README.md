# 📚 Book Tracker & Recommendation App

This is a FastAPI + Streamlit project that allows users to search for books, track their reading, and receive AI-generated book recommendations.

## Live Demo

Checkout the live application on Streamlit: [ReadRadar](https://booktracking-huv5uj2rm5ec4rqgbf6tgn.streamlit.app)

## Table of Contents
1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Configuration](#configuration)
5. [Technologies Used](#technologies-used)
6. [Contributing](#contributing)
7. [License](#license)
8. [Acknowledgments](#acknowledgments)

## 🚀 Features

- **📖 Search Books**: Search for books using the Google Books API.
- **📚 Track Your Reads**: Save books to a personal reading list.
- **🤖 AI Recommendations**: Get book recommendations based on your interests.
- **📊 Interactive UI**: A user-friendly interface built with Streamlit.

## 🛠️ Tech Stack
- Backend: FastAPI, PostgreSQL, Alembic (for migrations)
- Frontend: Streamlit
- External APIs: Google Books API, Marvin AI (for recommendations)
- Deployment: Fly.io (backend), Streamlit Cloud (frontend)


## 📡 API Endpoints

🔍 Book Search
GET /google-books/search?q={query}
Searches for books using the Google Books API.
Query Params: q (book title, author, or keyword)
Response: Returns a list of top 10 matching books.
📚 User Library
POST /books/
Adds a book to the user's personal collection.
Body: { "title": "Book Name", "author": "Author", "isbn": "123456789" }
Response: Returns the saved book details.
GET /books/
Retrieves all books in the user's saved collection.
DELETE /books/{book_id}
Removes a book from the collection.
Response: { "message": "Book deleted successfully" }
🤖 AI Recommendations
POST /recommendations/
Generates book recommendations based on a user's saved books.
Body: { "books": ["Book 1", "Book 2"] }
Response: A list of recommended books.
🤖 AI-Powered Book Recommendations

This app uses Marvin AI to generate personalized book recommendations.

🔹 How It Works:
The user saves books they’ve read or are interested in.
The backend sends this data to the AI recommendation system.
The AI suggests books based on themes, genres, and patterns.
📌 Example Output:

{
  "recommendations": [
    { "title": "The Hobbit", "author": "J.R.R. Tolkien" },
    { "title": "The Name of the Wind", "author": "Patrick Rothfuss" }
  ]
}
🎯 Installation & Setup

1. Clone the Repository
   '''bash
   git clone https://github.com/yourusername/book-tracker.git
   cd book-tracker
   '''
2️⃣ Set Up Backend (FastAPI)
Ensure you have Python installed, then create a virtual environment:

uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
Install dependencies:

uv pip install -r requirements.txt
Set up environment variables:

cp .env.example .env  # Then edit with your API keys and DB settings
Run database migrations:

alembic upgrade head
Start the FastAPI server:

uvicorn app.main:app --reload
3️⃣ Set Up Frontend (Streamlit)
Navigate to the frontend directory and install dependencies:

cd frontend
uv pip install -r requirements.txt
Run the Streamlit app:

streamlit run app.py
🌐 Deployment

Backend: Deployed on Fly.io
Frontend: Deployed on Streamlit Cloud
To deploy updates:

flyctl deploy  # For backend
git push origin main  # If frontend is linked to Streamlit Cloud
🔥 Future Features

📅 Reading progress tracking
🏆 Challenges & goals
📝 Personal notes & reviews
📝 Contributing

Want to contribute? Feel free to open issues or submit PRs!

📄 License

This project is licensed under the MIT License.

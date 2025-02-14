import requests
import streamlit as st

from config import settings

API_URL = settings.API_URL

st.set_page_config(page_title="Login", layout="centered")

st.title("🔑 Login")

st.sidebar.title("Navigation")

if st.session_state.access_token:
    pages = ["Search Books", "Saved Books", "AI Recommendations"]
else:
    pages = ["Login", "Search Books", "AI Recommendations"]

if "page" not in st.session_state or st.session_state.page not in pages:
    st.session_state.page = "Search Books"

page = st.sidebar.radio(
    "Go to",
    pages,
    index=pages.index(st.session_state.page),
)

if page != st.session_state.page:
    st.session_state.page = page

    if page == "Search Books":
        st.session_state.search_results = []
        st.session_state.last_search_query = ""

    match page:
        case "Search Books":
            st.switch_page("app.py")
        case "Saved Books":
            st.switch_page("pages/saved_books.py")
        case "AI Recommendations":
            st.switch_page("pages/ai_recommendations.py")
        case "Login":
            st.switch_page("pages/login.py")


with st.form("Login"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

    if submitted:
        response = requests.post(
            f"{API_URL}/auth/token",
            data={"username": username, "password": password},
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data["access_token"]
            st.session_state.username = username
            st.success(f"Welcome back, {username}!")
            st.switch_page("app.py")
        else:
            st.error("Invalid credentials. Please try again.")

st.page_link("pages/signup.py", label="Don't have an account? Sign up here.")

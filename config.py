import os

import streamlit as st
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    API_URL: str
    OPENAI_API_KEY: str
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    class Config:
        env_file = ".env"
        extra = "allow"


def load_settings():
    """Load settings from environment variables for FastAPI or from Streamlit secrets for Streamlit."""
    if os.getenv("FLY_APP_NAME"):  # Check if running in Fly.io (FastAPI)
        return Settings(
            SECRET_KEY=os.getenv("SECRET_KEY", "default_secret"),
            ALGORITHM=os.getenv("ALGORITHM", "HS256"),
            ACCESS_TOKEN_EXPIRE_MINUTES=int(
                os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
            ),
            API_URL=os.getenv("API_URL", "http://localhost:8000"),
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
            DATABASE_URL=os.getenv("DATABASE_URL", ""),
            POSTGRES_USER=os.getenv("POSTGRES_USER", ""),
            POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD", ""),
            POSTGRES_DB=os.getenv("POSTGRES_DB", ""),
        )
    elif "database" in st.secrets:  # Check if running in Streamlit
        print("✅ Found 'database' in secrets.")
        print(
            "🔹 DATABASE_URL from secrets:",
            st.secrets["database"].get("DATABASE_URL", "❌ Not Found"),
        )

        return Settings(
            SECRET_KEY=st.secrets.get("security", {}).get(
                "SECRET_KEY", "default_secret"
            ),
            ALGORITHM=st.secrets.get("security", {}).get("ALGORITHM", "HS256"),
            ACCESS_TOKEN_EXPIRE_MINUTES=st.secrets.get("security", {}).get(
                "ACCESS_TOKEN_EXPIRE_MINUTES", 30
            ),
            API_URL=st.secrets.get("api", {}).get("API_URL", "http://localhost:8000"),
            OPENAI_API_KEY=st.secrets.get("openai", {}).get("OPENAI_API_KEY", ""),
            DATABASE_URL=st.secrets.get("database", {}).get("DATABASE_URL", ""),
            POSTGRES_USER=st.secrets.get("database", {}).get("POSTGRES_USER", ""),
            POSTGRES_PASSWORD=st.secrets.get("database", {}).get(
                "POSTGRES_PASSWORD", ""
            ),
            POSTGRES_DB=st.secrets.get("database", {}).get("POSTGRES_DB", ""),
        )
    else:
        print("❌ No 'database' found in secrets.")
        return Settings()  # Default to .env values for local development


settings = load_settings()

# Ensure DATABASE_URL uses the correct prefix for SQLAlchemy
if settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace(
        "postgres://", "postgresql://", 1
    )

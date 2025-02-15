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


settings = Settings()

if "database" in st.secrets:
    settings = Settings(
        SECRET_KEY=st.secrets["security"]["SECRET_KEY"],
        ALGORITHM=st.secrets["security"]["ALGORITHM"],
        ACCESS_TOKEN_EXPIRE_MINUTES=st.secrets["security"][
            "ACCESS_TOKEN_EXPIRE_MINUTES"
        ],
        API_URL=st.secrets["api"]["API_URL"],
        OPENAI_API_KEY=st.secrets["openai"]["OPENAI_API_KEY"],
        DATABASE_URL=st.secrets["database"]["DATABASE_URL"],
        POSTGRES_USER=st.secrets["database"]["POSTGRES_USER"],
        POSTGRES_PASSWORD=st.secrets["database"]["POSTGRES_PASSWORD"],
        POSTGRES_DB=st.secrets["database"]["POSTGRES_DB"],
    )

if settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace(
        "postgres://", "postgresql://", 1
    )

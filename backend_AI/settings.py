from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    plagiarism_threshold: float = 0.5
    max_pdf_chars: int = 5000
    crossref_plagiarism_limit: int = 100
    crossref_doppelganger_limit: int = 50

    crossref_timeout: int = 15
    web_timeout: int = 10
    openai_timeout: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
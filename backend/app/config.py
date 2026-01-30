from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://tavi:tavi_password@localhost:5432/tavi_db"
    ENVIRONMENT: str = "development"

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None

    DEMO_TEST_EMAIL: Optional[str] = None
    DEMO_TEST_PHONE: Optional[str] = None
    PUBLIC_API_URL: Optional[str] = None

    GOOGLE_PLACES_API_KEY: Optional[str] = None
    YELP_API_KEY: Optional[str] = None

    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://frontend:3000",
        "https://tavi-frontend.onrender.com",
        "https://devoted-laughter-production-bc13.up.railway.app",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

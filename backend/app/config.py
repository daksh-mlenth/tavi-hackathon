from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://tavi:tavi_password@localhost:5432/tavi_db"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # AI APIs
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Communication APIs
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    
    # Demo/Testing - All messages go to these addresses
    DEMO_TEST_EMAIL: Optional[str] = None
    DEMO_TEST_PHONE: Optional[str] = None
    
    # Public URL for Twilio webhooks (use ngrok URL for local dev)
    PUBLIC_API_URL: Optional[str] = None
    
    # External APIs
    GOOGLE_PLACES_API_KEY: Optional[str] = None
    YELP_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://frontend:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

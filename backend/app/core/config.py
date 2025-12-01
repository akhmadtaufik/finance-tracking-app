import os
import json
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: list = json.loads(
        os.getenv("BACKEND_CORS_ORIGINS", '["http://localhost:5173", "http://localhost:3000", "http://localhost"]')
    )
    
    # Cookie Settings
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"


settings = Settings()

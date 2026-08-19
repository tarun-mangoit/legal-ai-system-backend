from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/legal_ai"
    JWT_SECRET: str = "supersecretkey"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GEMINI_API_KEY: str = "your_gemini_api_key"
    REDIS_URL: str = "redis://localhost:6379/0"
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "user@example.com"
    SMTP_PASSWORD: str = "secret"
    SMTP_FROM_NAME: str = "Legal AI System"
    SMTP_FROM_EMAIL: str = "noreply@legalai.com"
    RAZORPAY_KEY_ID: str = "your_razorpay_key_id"
    RAZORPAY_SECRET: str = "your_razorpay_secret"

    class Config:
        env_file = ".env"

settings = Settings()

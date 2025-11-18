from cryptography.fernet import Fernet
from dotenv import dotenv_values
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

# Load environment variables from config/.env into a dictionary
config = dotenv_values("config/.env")


class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True)

    # App
    APP_NAME: str = ""
    APP_ENVIRONMENT: str = "Developemnt"
    # DEBUG: bool = False
    # TODO :
    # Databases
    # MongoDB for user data
    MONGODB_URL: str = "mongodb://localhost:27017/"
    MONGO_DATABASE_NAME: str = "THE-REVIEW-USERS"

    # PostgreSQL for review data
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "thereview_reviews"

    @property
    def POSTGRES_URL(self) -> str:
        """Construct PostgreSQL connection URL for asyncpg"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def POSTGRES_URL_SYNC(self) -> str:
        """Construct PostgreSQL connection URL for synchronous connections (Alembic)"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Domain Name
    DOMAIN: str = "www.thereview.com"

    # REDIS FOR 2FA AND CACHING
    REDIS_HOST: str = "redis://localhost:6379"
    REDIS_CACHE_DB: int = 1  # Separate DB for caching (0 is for 2FA)

    # Cache TTL settings (in seconds)
    CACHE_TTL_SHORT: int = 300  # 5 minutes - for frequently changing data
    CACHE_TTL_MEDIUM: int = 1800  # 30 minutes - for review lists
    CACHE_TTL_LONG: int = 3600  # 1 hour - for aggregated stats
    CACHE_TTL_ENTITY: int = 7200  # 2 hours - for entity-specific data
    # JWT
    JWT_SECRET_KEY: str = "some_random_jwt_secret"

    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # PASSWORD ENTHROPY
    MIN_PASSWORD_ENTROPY: float = 64.0

    # GMAIL SERVICE
    GMAIL_ADDRESS: str = ""
    APP_PASSWORD: str = ""
    # FERNET
    FERNET_KEY: str = Fernet.generate_key().decode()
    # Security
    BCRYPT_ROUNDS: int = 12

    ALLOY_OTLP_ENDPOINT: str= "http://otel-collector:4317"


# Create settings instance and override with values from config dictionary
settings = Settings(**config)

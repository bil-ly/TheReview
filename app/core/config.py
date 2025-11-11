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
    # DEBUG: bool = False
    # TODO :
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017/"
    MONGO_DATABASE_NAME: str = "THE-REVIEW-USERS"

    # Domain Name
    DOMAIN: str = "www.thereview.com"

    # REDIS FOR 2FA
    REDIS_HOST: str = "redis://localhost:6379"
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


# Create settings instance and override with values from config dictionary
settings = Settings(**config)

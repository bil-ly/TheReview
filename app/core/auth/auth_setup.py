from auth_lib.auth_service import AuthService
from auth_lib.utils.email_service import DevEmailService
from auth_lib.utils.redis_utils import TwoFactorService
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.utils.mongo.user_repository import MongoUserRepository


def create_auth_service(database: AsyncIOMotorDatabase) -> AuthService:
    user_repository = MongoUserRepository(database)
    two_factor_service = TwoFactorService(settings.REDIS_HOST)
    email_service = DevEmailService()

    return AuthService(
        database=user_repository,
        jwt_secret=settings.JWT_SECRET_KEY,
        encryption_key=settings.FERNET_KEY,
        jwt_algorithm=settings.JWT_ALGORITHM,
        jwt_expires_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        min_password_entropy=settings.MIN_PASSWORD_ENTROPY,
        enable_2fa=False,
        two_factor_service=two_factor_service,
        email_service=email_service,
        domain=settings.DOMAIN,
        app_name=settings.APP_NAME,
    )

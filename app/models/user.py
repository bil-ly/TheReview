from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr

from app.utils.logger import get_logger

logger = get_logger("UserModel", log_to_std_out=True)


## USER ROLE
class UserRole(str, Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"


@dataclass
class User:
    full_name: str = ""
    username: str = ""
    email: str = ""
    hashed_password: str = ""
    role: UserRole = UserRole.REVIEWER
    is_active: bool = True
    two_factor_enabled: bool = False

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class UserCreate(BaseModel):
    """Data required from a user to sign up."""

    username: str
    email: str
    full_name: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str
    totp_code: str | None = None


class CreateUserModel(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str | None = None
    role: UserRole
    is_active: bool | None = True


class UpdateUserModel(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class CustomPermissionModel(BaseModel):
    can_create: list[UserRole] | None = None
    can_view: list[UserRole] | None = None
    can_update: list[UserRole] | None = None
    can_delete: list[UserRole] | None = None
    can_manage_all: bool | None = None


## Password schemas
# TODO : REMOVE THE MODEL FROM THIS SCRIPT
class PasswordResetRequestModel(BaseModel):
    email: EmailStr


class PasswordResetConfirmModel(BaseModel):
    new_password: str


# In-memory storage for custom permissions : TODO : I WILL PERSIST IT IN THE DB WHEN THE APP GOES LIVE
USER_CUSTOM_PERMISSIONS: dict[str, dict[str, Any]] = {}


# Default permission matrix , for when i want to add custgom permmisions later on
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        "can_create": [UserRole.ADMIN, UserRole.REVIEWER],
        "can_view": [UserRole.ADMIN, UserRole.REVIEWER],
        "can_update": [UserRole.ADMIN, UserRole.REVIEWER],
        "can_delete": [UserRole.ADMIN, UserRole.REVIEWER],
        "can_manage_all": True,
    },
    UserRole.REVIEWER: {
        "can_create": [],
        "can_view": [],
        "can_update": [],
        "can_delete": [],
        "can_manage_all": False,
    },
}

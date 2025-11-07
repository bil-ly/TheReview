from __future__ import annotations
from enum import Enum

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
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
    role: UserRole= UserRole.REVIEWER
    is_active: bool = True
    two_factor_enabled: bool = False

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    """Data required from a user to sign up."""

    username: str
    email: str
    full_name: str
    password: str    

class UserLogin(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None 
    
class CreateUserModel(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: Optional[bool] = True

class UpdateUserModel(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class CustomPermissionModel(BaseModel):
    can_create: Optional[List[UserRole]] = None
    can_view: Optional[List[UserRole]] = None
    can_update: Optional[List[UserRole]] = None
    can_delete: Optional[List[UserRole]] = None
    can_manage_all: Optional[bool] = None


## Password schemas
# TODO : REMOVE THE MODEL FROM THIS SCRIPT
class PasswordResetRequestModel(BaseModel):
    email: EmailStr

class PasswordResetConfirmModel(BaseModel):
    new_password: str

# In-memory storage for custom permissions : TODO : I WILL PERSIST IT IN THE DB WHEN THE APP GOES LIVE
USER_CUSTOM_PERMISSIONS: Dict[str, Dict[str, Any]] = {}



# Default permission matrix , for when i want to add custgom permmisions later on
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        "can_create": [UserRole.ADMIN, UserRole.REVIEWER],
        "can_view": [UserRole.ADMIN, UserRole.REVIEWER],
        "can_update": [UserRole.ADMIN, UserRole.REVIEWER],
        "can_delete": [UserRole.ADMIN, UserRole.REVIEWER],
        "can_manage_all": True
    },
    UserRole.REVIEWER: {
        "can_create": [],
        "can_view": [],
        "can_update": [],
        "can_delete": [],
        "can_manage_all": False 
    }
}
from typing import Any

from fastapi import Depends, HTTPException

from app.models.user import (
    ROLE_PERMISSIONS,
    USER_CUSTOM_PERMISSIONS,
    UserRole,
)
from app.utils.dependencies import get_current_user_dependency


def get_user_role(user: dict[str, Any]) -> UserRole:
    return UserRole(user.get("role", UserRole.REVIEWER))


def get_user_permissions(user: dict[str, Any]) -> dict[str, Any]:
    """Merge role permissions with custom overrides"""
    role = get_user_role(user)
    base = ROLE_PERMISSIONS.get(role, {})
    custom = USER_CUSTOM_PERMISSIONS.get(user["_id"], {})
    return {**base, **custom}


def check_permission(current_user: dict[str, Any], target_role: UserRole, action: str) -> bool:
    perms = get_user_permissions(current_user)

    if action == "create":
        return target_role in perms.get("can_create", []) or (
            perms.get("can_manage_all", False) and target_role != UserRole.ADMIN
        )
    elif action == "view":
        return target_role in perms.get("can_view", []) or (
            perms.get("can_manage_all", False) and target_role != UserRole.ADMIN
        )
    elif action == "update":
        return target_role in perms.get("can_update", []) or (
            perms.get("can_manage_all", False) and target_role != UserRole.ADMIN
        )
    elif action == "delete":
        return target_role in perms.get("can_delete", []) or (
            perms.get("can_manage_all", False) and target_role != UserRole.ADMIN
        )

    return False


def require_permission(action: str, target_role: UserRole = None):
    def checker(current_user=Depends(get_current_user_dependency)):
        if target_role and not check_permission(current_user, target_role, action):
            raise HTTPException(
                status_code=403,
                detail=f"{get_user_role(current_user).value} cannot {action} {target_role.value} accounts",
            )
        return current_user

    return checker

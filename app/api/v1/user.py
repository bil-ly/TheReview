from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from fastapi import Query
from utils.dependencies import get_auth_service, get_current_user_dependency
from models.user import UserRole, ROLE_PERMISSIONS, USER_CUSTOM_PERMISSIONS, CreateUserModel , UpdateUserModel , CustomPermissionModel

router = APIRouter(prefix="/users", tags=["user-management"])

def get_user_role(user: Dict[str, Any]) -> UserRole:
    return UserRole(user.get("role", UserRole.STUDENT))

def get_user_permissions(user: Dict[str, Any]) -> Dict[str, Any]:
    """Merge role permissions with custom overrides"""
    role = get_user_role(user)
    base = ROLE_PERMISSIONS.get(role, {})
    custom = USER_CUSTOM_PERMISSIONS.get(user["_id"], {})
    return {**base, **custom}

def check_permission(current_user: Dict[str, Any], target_role: UserRole, action: str) -> bool:
    perms = get_user_permissions(current_user)
    
    # Prevent teachers from managing admins
    if get_user_role(current_user) == UserRole.TEACHER and target_role == UserRole.ADMIN:
        return False

    if action == "create":
        return target_role in perms.get("can_create", []) or (perms.get("can_manage_all", False) and target_role != UserRole.ADMIN)
    elif action == "view":
        return target_role in perms.get("can_view", []) or (perms.get("can_manage_all", False) and target_role != UserRole.ADMIN)
    elif action == "update":
        return target_role in perms.get("can_update", []) or (perms.get("can_manage_all", False) and target_role != UserRole.ADMIN)
    elif action == "delete":
        return target_role in perms.get("can_delete", []) or (perms.get("can_manage_all", False) and target_role != UserRole.ADMIN)
    
    return False

def require_permission(action: str, target_role: UserRole = None):
    def checker(current_user = Depends(get_current_user_dependency)):
        if target_role and not check_permission(current_user, target_role, action):
            raise HTTPException(
                status_code=403,
                detail=f"{get_user_role(current_user).value} cannot {action} {target_role.value} accounts"
            )
        return current_user
    return checker


@router.post("/create")
async def create_user(user_data: CreateUserModel,
                      auth_service = Depends(get_auth_service),
                      current_user = Depends(get_current_user_dependency)):
    if not check_permission(current_user, user_data.role, "create"):
        raise HTTPException(status_code=403, detail=f"Cannot create {user_data.role.value} account")
    
    result = await auth_service.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role.value,
        is_active=user_data.is_active
    )
    return {"message": f"{user_data.role.value.title()} created", "user_id": result["_id"]}

@router.put("/{user_id}")
async def update_user(user_id: str,
                      update_data: UpdateUserModel,
                      auth_service = Depends(get_auth_service),
                      current_user = Depends(get_current_user_dependency)):
    user = await auth_service.database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    target_role = get_user_role(user)
    
    if current_user["_id"] != user_id and not check_permission(current_user, target_role, "update"):
        raise HTTPException(status_code=403, detail="Cannot update this user")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    if update_dict:
        update_dict["updated_at"] = datetime.now(timezone.utc)
        await auth_service.database.update_user(user_id, update_dict)
    
    return {"message": "User updated successfully", "user_id": user_id}

@router.delete("/{user_id}")
async def delete_user(user_id: str,
                      auth_service = Depends(get_auth_service),
                      current_user = Depends(get_current_user_dependency)):
    user = await auth_service.database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not check_permission(current_user, get_user_role(user), "delete"):
        raise HTTPException(status_code=403, detail="Cannot delete this user")
    
    await auth_service.database.update_user(user_id, {"is_active": False, "deleted_at": datetime.now(timezone.utc)})
    return {"message": "User deleted", "user_id": user_id}


@router.patch("/{user_id}/permissions")
async def assign_custom_permissions(user_id: str,
                                    permissions_data: CustomPermissionModel,
                                    auth_service = Depends(get_auth_service),
                                    current_user = Depends(require_permission("update", UserRole.TEACHER))):
    """Admin assigns custom permissions to a teacher"""
    user = await auth_service.database.get_user_by_id(user_id)
    if not user or get_user_role(user) != UserRole.TEACHER:
        raise HTTPException(status_code=400, detail="Custom permissions can only be assigned to teachers")
    
    new_perms = {k: v for k, v in permissions_data.dict(exclude_unset=True).items()}
    USER_CUSTOM_PERMISSIONS[user_id] = new_perms
    return {"message": "Custom permissions updated", "user_id": user_id, "permissions": new_perms}

@router.get("/list")
async def list_users(
    role: Optional[UserRole] = Query(None, description="Filter users by role"),
    auth_service = Depends(get_auth_service),
    current_user = Depends(get_current_user_dependency)
):
    """
    List all users with optional filtering by role.
    Permissions:
      - Admin: can see all users
      - Teacher: can only see students
      - Student: cannot list others
    """
    try:
        if get_user_role(current_user) == UserRole.ADMIN:
            allowed_roles = [UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT]
        elif get_user_role(current_user) == UserRole.TEACHER:
            allowed_roles = [UserRole.STUDENT]
        else:
            raise HTTPException(status_code=403, detail="Insufficient permissions to list users")

        if role:
            if role not in allowed_roles:
                raise HTTPException(status_code=403, detail=f"You cannot view {role.value} users")
            allowed_roles = [role]

        users = await auth_service.database.list_users_by_roles(allowed_roles)

        return [
            {
                "id": u["_id"],
                "username": u["username"],
                "email": u["email"],
                "full_name": u.get("full_name"),
                "role": u.get("role"),
                "is_active": u.get("is_active", True)
            }
            for u in users
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
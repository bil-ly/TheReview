from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.user import (
    CreateUserModel,
    UpdateUserModel,
    UserRole,
)
from app.utils.dependencies import get_auth_service, get_current_user_dependency
from app.utils.user_managemet import check_permission, get_user_role

router = APIRouter(prefix="/users", tags=["user-management"])


@router.post("/create")
async def create_user(
    user_data: CreateUserModel,
    auth_service=Depends(get_auth_service),
    current_user=Depends(get_current_user_dependency),
):
    if not check_permission(current_user, user_data.role, "create"):
        raise HTTPException(status_code=403, detail=f"Cannot create {user_data.role.value} account")

    result = await auth_service.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role.value,
        is_active=user_data.is_active,
    )
    return {"message": f"{user_data.role.value.title()} created", "user_id": result["_id"]}


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    update_data: UpdateUserModel,
    auth_service=Depends(get_auth_service),
    current_user=Depends(get_current_user_dependency),
):
    user = await auth_service.database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    target_role = get_user_role(user)

    if current_user["_id"] != user_id and not check_permission(current_user, target_role, "update"):
        raise HTTPException(status_code=403, detail="Cannot update this user")

    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    if update_dict:
        update_dict["updated_at"] = datetime.now(UTC)
        await auth_service.database.update_user(user_id, update_dict)

    return {"message": "User updated successfully", "user_id": user_id}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    auth_service=Depends(get_auth_service),
    current_user=Depends(get_current_user_dependency),
):
    user = await auth_service.database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not check_permission(current_user, get_user_role(user), "delete"):
        raise HTTPException(status_code=403, detail="Cannot delete this user")

    await auth_service.database.update_user(
        user_id, {"is_active": False, "deleted_at": datetime.now(UTC)}
    )
    return {"message": "User deleted", "user_id": user_id}


@router.get("/list")
async def list_users(
    role: UserRole | None = Query(None, description="Filter users by role"),
    auth_service=Depends(get_auth_service),
    current_user=Depends(get_current_user_dependency),
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
            allowed_roles = [UserRole.ADMIN, UserRole.REVIEWER]
        elif get_user_role(current_user) == UserRole.REVIEWER:
            allowed_roles = [UserRole.REVIEWER]
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
                "is_active": u.get("is_active", True),
            }
            for u in users
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

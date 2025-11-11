from auth_lib.auth_service import AuthService
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# HTTP Bearer token scheme
security = HTTPBearer()


def get_auth_service(request: Request) -> AuthService:
    """Dependency to get auth service from app state"""
    auth_service = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        raise HTTPException(status_code=500, detail="Auth service not initialized")
    return auth_service


async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Dependency to get current user from JWT token
    Extracts token from Authorization header and validates it
    """
    try:
        token = credentials.credentials

        current_user = await auth_service.get_current_user_from_token(token)

        return current_user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

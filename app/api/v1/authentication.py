from fastapi import APIRouter, Depends, HTTPException , status
from models.user import UserCreate , UserLogin , PasswordResetConfirmModel, PasswordResetRequestModel
from utils.dependencies import get_auth_service
from models.student import Student
from typing import Dict, Any
from utils.dependencies import get_auth_service, get_current_user_dependency
from fastapi.responses import JSONResponse
from dataclasses import asdict


router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register")
async def register_user(
    user_data: UserCreate,
    auth_service = Depends(get_auth_service)
):
    """Register a new user and create a corresponding student record"""
    try:
        result = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            username=user_data.username,
            full_name=user_data.full_name,
            role="student" 
        )

        user_id = result["_id"]

        student_data = Student(
            user_id=user_id,
            subjects=[] 
        )

        student_dict = asdict(student_data)

        await auth_service.database.db.students.insert_one(student_dict)

        return {
            "message": "User registered successfully",
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")
    


@router.post("/login")
async def login_user(
    login_data: UserLogin,
    auth_service = Depends(get_auth_service) 
):
    """Login user and return JWT token"""
    try:
        result: Dict[str, Any] = await auth_service.login_user(
            username=login_data.username,
            password=login_data.password,
            totp_code=login_data.totp_code
        )
        print(login_data.username)
        return result 
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=401, detail=f"Login failed {e}")
    

# -- 2FA --
@router.post("/2fa/enable")
async def enable_2fa(
    current_user=Depends(get_current_user_dependency),
    auth_service = Depends(get_auth_service)
):
    """Enable 2FA for current user"""
    try:
        return await auth_service.enable_2fa_for_user(str(current_user["_id"]))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"2FA enable failed {e}")


@router.post("/password-reset-request")
async def password_reset_request(
    email_data: PasswordResetRequestModel,
    auth_service = Depends(get_auth_service)
):
    """
    Request password reset - generates token and sends email
    
    Args:
        email_data: Email address for password reset
        auth_service: AuthService dependency
        
    Returns:
        Success message (always returns success for security)
    """
    try:
        token = await auth_service.reset_password_request(email_data.email)
        return JSONResponse(
            content={
                "message": "If this email exists in our system, you will receive password reset instructions."
            },
            status_code=status.HTTP_200_OK
        )
    except HTTPException as e:
        if e.status_code == 404:
            return JSONResponse(
                content={
                    "message": "If this email exists in our system, you will receive password reset instructions."
                },
                status_code=status.HTTP_200_OK
            )
        raise
    except Exception as e:
        import traceback
        print(f"Password reset request error: {traceback.format_exc()}")
        return JSONResponse(
            content={
                "message": "If this email exists in our system, you will receive password reset instructions."
            },
            status_code=status.HTTP_200_OK
        )

@router.post("/password-reset-confirm/{token}")
async def password_reset_confirm(
    token: str,
    passwords: PasswordResetConfirmModel,
    auth_service = Depends(get_auth_service)
):
    """
    Confirm password reset with token
    
    Args:
        token: Password reset token from email
        passwords: New password data
        auth_service: AuthService dependency
        
    Returns:
        Success message if password was reset
        
    Raises:
        HTTPException: If token is invalid or password is weak
    """
    try:
        success = await auth_service.reset_password(token, passwords.new_password)
        
        if success:
            return JSONResponse(
                content={"message": "Password reset successfully"},
                status_code=status.HTTP_200_OK
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset failed"
            )
    #TODO : Remove the Extra Exception Later        
    except HTTPException:
        # Re-raise HTTP exceptions as they contain proper status codes
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
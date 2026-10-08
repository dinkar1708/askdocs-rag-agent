"""Authentication and User Management Endpoints"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import (
    get_current_active_user,
    require_role,
    verify_api_key,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    PasswordChange,
    UserListResponse,
)
from app.services.audit import log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.
    """
    existing_user = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    # First user registered can be automatically an admin if no users exist
    user_count = db.query(User).count()
    role = "admin" if user_count == 0 else (user_data.role if user_data.role in ("admin", "user", "viewer") else "user")

    hashed = hash_password(user_data.password)
    user = User(
        email=user_data.email.lower(),
        hashed_password=hashed,
        full_name=user_data.full_name,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="USER_REGISTER",
        user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email, "role": user.role}
    )

    logger.info(f"Registered new user: {user.email} (role: {user.role})")
    return user


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and issue a JWT access token.
    """
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        log_audit_event(
            db=db,
            action="AUTH_FAILURE",
            resource_type="auth",
            details={"email": login_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        log_audit_event(
            db=db,
            action="AUTH_DEACTIVATED",
            user_id=user.id,
            resource_type="user",
            details={"email": user.email}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact administrator.",
        )

    token = create_access_token({
        "sub": user.email,
        "user_id": user.id,
        "role": user.role,
    })

    log_audit_event(
        db=db,
        action="USER_LOGIN",
        user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user,
    )


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get profile of the currently authenticated user.
    """
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Change password for the currently authenticated user.
    """
    if not verify_password(password_data.old_password, current_user.hashed_password):
        log_audit_event(
            db=db,
            action="PASSWORD_CHANGE_FAILURE",
            user_id=current_user.id,
            resource_type="user",
            resource_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()

    log_audit_event(
        db=db,
        action="PASSWORD_CHANGE_SUCCESS",
        user_id=current_user.id,
        resource_type="user",
        resource_id=str(current_user.id)
    )
    return {"message": "Password changed successfully"}


@router.get("/users", response_model=UserListResponse, dependencies=[Depends(require_role("admin"))])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    List all users (Admin only).
    """
    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(User).count()
    return UserListResponse(users=users, total=total)

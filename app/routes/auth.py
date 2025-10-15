"""Authentication and authorization endpoints"""

import logging
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, APIKey, UserRole
from ..schemas import (
    UserCreate, UserResponse, UserUpdate,
    Token, LoginRequest, RefreshTokenRequest,
    APIKeyCreate, APIKeyResponse, APIKeyListItem,
    AuditLogResponse
)
from ..auth import (
    get_password_hash, authenticate_user, create_access_token, create_refresh_token,
    decode_token, get_current_active_user, require_admin, generate_api_key
)
from ..audit import log_audit_event, get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        log_audit_event(
            db, "register", "failure",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"reason": "username_exists", "username": user_data.username}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        log_audit_event(
            db, "register", "failure",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"reason": "email_exists", "email": user_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=UserRole.USER  # Default role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    log_audit_event(
        db, "register", "success",
        user_id=db_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    logger.info(f"New user registered: {db_user.username}")
    return db_user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT tokens"""
    user = authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        log_audit_event(
            db, "login", "failure",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"username": login_data.username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        log_audit_event(
            db, "login", "failure",
            user_id=user.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"reason": "inactive_account"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Create tokens
    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role.value
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    log_audit_event(
        db, "login", "success",
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        token_data = decode_token(refresh_data.refresh_token)
    except HTTPException:
        log_audit_event(
            db, "token_refresh", "failure",
            ip_address=get_client_ip(request),
            details={"reason": "invalid_token"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    new_token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role.value
    }
    
    access_token = create_access_token(new_token_data)
    new_refresh_token = create_refresh_token(new_token_data)
    
    log_audit_event(
        db, "token_refresh", "success",
        user_id=user.id,
        ip_address=get_client_ip(request)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.email is not None:
        # Check if email is already taken
        existing = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = user_update.email
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    log_audit_event(
        db, "profile_update", "success",
        user_id=current_user.id,
        ip_address=get_client_ip(request)
    )
    
    return current_user


# API Key Management
@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for programmatic access"""
    key = generate_api_key()
    
    expires_at = None
    if api_key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_in_days)
    
    api_key = APIKey(
        key=key,
        name=api_key_data.name,
        user_id=current_user.id,
        expires_at=expires_at
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    log_audit_event(
        db, "create_api_key", "success",
        user_id=current_user.id,
        resource=f"api_key:{api_key.id}",
        ip_address=get_client_ip(request)
    )
    
    logger.info(f"API key created for user {current_user.username}: {api_key.name}")
    return api_key


@router.get("/api-keys", response_model=List[APIKeyListItem])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all API keys for current user"""
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    return api_keys


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    db.delete(api_key)
    db.commit()
    
    log_audit_event(
        db, "delete_api_key", "success",
        user_id=current_user.id,
        resource=f"api_key:{key_id}",
        ip_address=get_client_ip(request)
    )
    
    return {"message": "API key deleted successfully"}


# Admin endpoints
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    users = db.query(User).all()
    return users


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = 100,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get audit logs (admin only)"""
    from ..models import AuditLog
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return logs


"""
FastAPI Dependency Injection Functions
Handles authentication, database sessions, and other shared dependencies
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate JWT token and return current user.
    If LOGIN_DISABLED is True, bypass authentication.

    Args:
        credentials: JWT bearer token from Authorization header
        db: Database session

    Returns:
        dict: User information from token

    Raises:
        HTTPException: If token is invalid or missing (when login is enabled)
    """
    # If login is disabled, return a mock admin user
    if settings.is_login_disabled():
        return {
            "username": "admin",
            "user_id": 1,
            "is_admin": True,
            "auth_disabled": True
        }

    # Login is enabled, validate token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "username": username,
            "user_id": user_id,
            "is_admin": payload.get("is_admin", False),
            "auth_disabled": False
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin(
    current_user: dict = Depends(get_current_user)
):
    """
    Ensure current user is an admin.

    Args:
        current_user: Current user from get_current_user

    Returns:
        dict: Admin user information

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# Optional authentication (doesn't raise error if no token)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that work differently for authenticated users.

    Args:
        credentials: JWT bearer token (optional)
        db: Database session

    Returns:
        Optional[dict]: User information or None
    """
    if settings.is_login_disabled():
        return {
            "username": "admin",
            "user_id": 1,
            "is_admin": True,
            "auth_disabled": True
        }

    if not credentials:
        return None

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        return {
            "username": payload.get("sub"),
            "user_id": payload.get("user_id"),
            "is_admin": payload.get("is_admin", False),
            "auth_disabled": False
        }
    except JWTError:
        return None

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
import asyncpg

from ..core.database import get_db_conn
from ..core.config import settings
from ..core.security import (
    hash_password, verify_password, create_access_token, 
    get_current_user, create_refresh_token, hash_token, limiter
)
from ..schemas.user import UserCreate, UserResponse, Token
from ..repositories.user_repo import UserRepository
from ..repositories.wallet_repo import WalletRepository
from ..repositories.token_repo import RefreshTokenRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE_NAME = "refresh_token"
# Use root path so reverse proxies (e.g., /api prefix) still send the cookie
REFRESH_COOKIE_PATH = "/"


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Create a new user account with email and password."
)
@limiter.limit("3/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    _ = request.client  # touch request to satisfy rate limiter usage
    user_repo = UserRepository(conn)
    wallet_repo = WalletRepository(conn)
    
    # Check if user already exists
    existing = await user_repo.get_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    password_hash = hash_password(user_data.password)
    user = await user_repo.create(user_data.email, user_data.username, password_hash)
    
    # Create default wallet for user
    await wallet_repo.create(user["id"], "Dompet Utama")
    
    return user


@router.post(
    "/token",
    response_model=Token,
    summary="Login",
    description="""
Authenticate user and receive tokens.

**Returns:**
- `access_token` in JSON response (15 min lifetime)
- `refresh_token` in HTTPOnly cookie (7 day lifetime)
    """
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    user_repo = UserRepository(conn)
    token_repo = RefreshTokenRepository(conn)
    
    # Validate credentials
    user = await user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user["id"])})
    refresh_token = create_refresh_token()
    
    # Store refresh token hash in DB
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    user_agent = request.headers.get("user-agent", "")[:255]
    ip_address = request.client.host if request.client else None
    
    await token_repo.create(
        user_id=user["id"],
        token_hash=hash_token(refresh_token),
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    # Set HTTPOnly cookie for refresh token
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh Access Token",
    description="""
Exchange a valid refresh token for a new access token.

**Token Rotation:**
- The old refresh token is revoked
- A new refresh token is issued and stored in cookie
- This prevents token reuse attacks
    """
)
async def refresh_access_token(
    request: Request,
    response: Response,
    refresh_token: str = Cookie(None, alias=REFRESH_COOKIE_NAME),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
    
    token_repo = RefreshTokenRepository(conn)
    old_hash = hash_token(refresh_token)
    
    # Validate the old token
    stored = await token_repo.get_by_hash(old_hash)
    if not stored:
        # Token invalid or already revoked - potential reuse attack
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # TOKEN ROTATION: Revoke the old token
    await token_repo.revoke(old_hash)
    
    # Generate new tokens
    new_access_token = create_access_token(data={"sub": str(stored["user_id"])})
    new_refresh_token = create_refresh_token()
    
    # Store new refresh token
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    user_agent = request.headers.get("user-agent", "")[:255]
    ip_address = request.client.host if request.client else None
    
    await token_repo.create(
        user_id=stored["user_id"],
        token_hash=hash_token(new_refresh_token),
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    # Update cookie with new refresh token
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=new_refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH
    )
    
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post(
    "/logout",
    summary="Logout",
    description="Revoke the current refresh token and clear the cookie."
)
async def logout(
    response: Response,
    refresh_token: str = Cookie(None, alias=REFRESH_COOKIE_NAME),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    if refresh_token:
        token_repo = RefreshTokenRepository(conn)
        await token_repo.revoke(hash_token(refresh_token))
    
    # Delete the cookie
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    
    return {"message": "Logged out successfully"}


@router.post(
    "/logout-all",
    summary="Logout All Devices",
    description="Revoke all refresh tokens for the current user (logout from all devices)."
)
async def logout_all_devices(
    response: Response,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    token_repo = RefreshTokenRepository(conn)
    revoked_count = await token_repo.revoke_all_for_user(current_user["id"])
    
    # Delete current cookie
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    
    return {"message": f"Logged out from {revoked_count} device(s)"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="Get the profile of the currently authenticated user."
)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.get(
    "/sessions",
    summary="Get Active Sessions",
    description="List all active login sessions for the current user."
)
async def get_sessions(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    token_repo = RefreshTokenRepository(conn)
    sessions = await token_repo.get_active_sessions(current_user["id"])
    return {"sessions": sessions}

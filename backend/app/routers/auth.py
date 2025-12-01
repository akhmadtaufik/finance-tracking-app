from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import asyncpg

from ..core.database import get_db_conn
from ..core.security import hash_password, verify_password, create_access_token, get_current_user
from ..schemas.user import UserCreate, UserResponse, Token
from ..repositories.user_repo import UserRepository
from ..repositories.wallet_repo import WalletRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, conn: asyncpg.Connection = Depends(get_db_conn)):
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


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    user_repo = UserRepository(conn)
    
    user = await user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user["id"])})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

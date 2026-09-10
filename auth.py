"""
auth.py
=======
Authentication and Security Module:
- Salted password hashing via bcrypt
- JSON Web Token (JWT) encoding & decoding
- FastAPI Dependency Injection for Protected Routes (get_current_user & get_optional_user)
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from database import get_db
from models import User

# Load config from environment. JWT_SECRET_KEY has NO hardcoded fallback on
# purpose: a secret baked into source control is a secret anyone reading this
# repo already knows, which lets them forge valid tokens for any user. Set
# JWT_SECRET_KEY in your .env before running the app.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not set. Add a long random value to your .env file "
        "(e.g. `python -c \"import secrets; print(secrets.token_hex(32))\"`)."
    )
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 1440))  # 24 hours

# OAuth2 scheme with optional header parsing
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


import secrets

# --- Pydantic Schemas ---
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)


class UserLoginRequest(BaseModel):
    email_or_username: str
    password: str


class EmailVerifyRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)
    code: str = Field(..., min_length=6, max_length=6)


class ResendCodeRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_verified: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


def generate_verification_code() -> str:
    """Generates a cryptographically secure 6-digit numeric verification code."""
    return f"{secrets.randbelow(900000) + 100000}"


# --- Password Utilities (Direct bcrypt for speed & safety) ---
def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with automatic salt."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against its bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False


# --- JWT Utilities ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT access token. Returns payload dict or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


# --- FastAPI Dependencies ---
def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Enforces authentication. Raises 401 Unauthorized if token is missing or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def get_optional_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    """
    Optional authentication for guest-friendly routes.
    Returns the User object if a valid token is provided, or None if guest.
    """
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        return None

    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user if (user and user.is_active) else None
    except Exception:
        return None

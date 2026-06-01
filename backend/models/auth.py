"""
models/auth.py — Pydantic models for auth (backward compat aliases).
The canonical models are now defined in routers/auth.py as UserOut.
These are kept for any external references.
"""

from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: str = ""
    is_verified: bool = False
    is_guest: Optional[bool] = False
    usage_count: Optional[int] = None
    usage_limit: Optional[int] = None
    limit_exceeded: Optional[bool] = None

    class Config:
        from_attributes = True


class OTPRequest(BaseModel):
    email: str


class OTPVerify(BaseModel):
    email: str
    otp: str
    new_password: Optional[str] = None

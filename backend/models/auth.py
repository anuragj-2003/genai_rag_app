from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    is_verified: bool = False
    is_guest: Optional[bool] = False
    usage_count: Optional[int] = None
    usage_limit: Optional[int] = None
    limit_exceeded: Optional[bool] = None
    
    class Config:
        from_attributes = True

# OTP Models
class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    otp: str
    new_password: Optional[str] = None # For reset password flow

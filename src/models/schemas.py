from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    login: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=72)


class UserLogin(BaseModel):
    login: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ProfileUpdate(BaseModel):
    login: Optional[str] = Field(None, min_length=3, max_length=255)
    password: Optional[str] = Field(None, min_length=6, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)


class RoleUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)


class RoleAssign(BaseModel):
    user_id: str
    role_name: str


class RoleCheck(BaseModel):
    user_id: str
    role_name: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ChangeLoginRequest(BaseModel):
    new_login: str


class BookmarkCreate(BaseModel):
    movie_id: str = Field(..., min_length=1, max_length=255)


class BookmarkOut(BaseModel):
    id: str
    user_id: str
    movie_id: str
    created_at: datetime
    updated_at: datetime


class LikeCreate(BaseModel):
    movie_id: str = Field(..., min_length=1, max_length=255)


class LikeOut(BaseModel):
    id: str
    user_id: str
    movie_id: str
    created_at: datetime
    updated_at: datetime


class ReviewCreate(BaseModel):
    movie_id: str = Field(..., min_length=1, max_length=255)
    text: str = Field(..., min_length=1, max_length=5000)
    rating: int = Field(..., ge=1, le=10)


class ReviewUpdate(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    rating: int = Field(..., ge=1, le=10)


class ReviewOut(BaseModel):
    id: str
    user_id: str
    movie_id: str
    text: str
    rating: int
    created_at: datetime
    updated_at: datetime

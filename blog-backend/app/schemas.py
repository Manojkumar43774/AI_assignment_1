from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from .moderation import censor


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    bio: str | None = None
    avatar_url: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    has_password: bool = False

    model_config = {"from_attributes": True}


class SignupRequestOtp(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_]+$")
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)

    @field_validator("first_name", "last_name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        return censor(value)


class SignupVerifyOtp(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequestOtp(BaseModel):
    email: EmailStr


class PasswordResetVerify(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=255)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageOut(BaseModel):
    message: str


class PublicUserOut(BaseModel):
    id: int
    username: str
    bio: str | None = None
    avatar_url: str | None = None
    blog_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    bio: str | None = Field(default=None, max_length=500)

    @field_validator("bio")
    @classmethod
    def _validate_bio(cls, value: str | None) -> str | None:
        return censor(value)


class ChangePasswordRequest(BaseModel):
    old_password: str | None = None
    new_password: str = Field(min_length=8, max_length=255)


class BlogCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    is_draft: bool = False

    @field_validator("title", "content")
    @classmethod
    def _validate_blog_fields(cls, value: str) -> str:
        return censor(value)


class BlogUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    is_draft: bool | None = None

    @field_validator("title", "content")
    @classmethod
    def _validate_blog_fields(cls, value: str) -> str:
        return censor(value)


class BlogOut(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    author_username: str
    author_avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    like_count: int = 0
    comment_count: int = 0
    liked_by_me: bool = False
    is_draft: bool = False

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: int
    content: str
    user_id: int
    username: str
    avatar_url: str | None = None
    blog_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class LikeOut(BaseModel):
    liked: bool
    like_count: int

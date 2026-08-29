from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "ar"
    label_id: str | None = None


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    role: str | None = None
    label_id: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    label_id: str | None = None
    is_active: bool
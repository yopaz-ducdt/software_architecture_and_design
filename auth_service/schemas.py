from pydantic import BaseModel, EmailStr
from typing import Optional


class CustomerRegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class StaffRegisterRequest(BaseModel):
    name: str
    username: str
    password: str
    role: str = "staff"


class CustomerLoginRequest(BaseModel):
    email: str
    password: str


class StaffLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    user_id: int
    name: str
    role: Optional[str] = None


class CustomerOut(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True


class StaffOut(BaseModel):
    id: int
    name: str
    username: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

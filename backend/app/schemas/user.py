import uuid
from datetime import date, datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    position: str | None = None
    phone: str | None = None
    salary: float | None = None
    hire_date: date | None = None
    department_id: str | None = None
    manager_id: str | None = None


class UserCreate(UserBase):
    password: str
    role: str = "employee"


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    position: str | None = None
    phone: str | None = None
    hire_date: date | None = None
    department_id: str | None = None
    manager_id: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: str
    position: str | None
    salary: float | None
    phone: str | None
    hire_date: date | None
    department_id: uuid.UUID | None
    manager_id: uuid.UUID | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserOrgResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    role: str
    position: str | None
    department_name: str | None
    manager_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    email: str
    password: str

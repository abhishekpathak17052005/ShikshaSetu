from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AccessRole(StrEnum):
    EMPLOYEE = "EMPLOYEE"
    ADMIN = "ADMIN"


def normalize_email(value: str) -> str:
    return value.strip().lower()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=200)
    role_id: str = Field(min_length=1)
    designation: str = Field(min_length=1, max_length=200)
    department: str = Field(min_length=1, max_length=200)
    employee_id: str = Field(min_length=1, max_length=100)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_value(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("full_name", "designation", "department", "employee_id")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_value(cls, value: str) -> str:
        return normalize_email(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    role_id: str
    designation: str
    department: str
    employee_id: str
    status: str
    access_role: AccessRole


class UserProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    designation: str | None = Field(default=None, min_length=1, max_length=200)
    department: str | None = Field(default=None, min_length=1, max_length=200)
    employee_id: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("full_name", "designation", "department", "employee_id")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

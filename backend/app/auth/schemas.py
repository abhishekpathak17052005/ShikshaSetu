from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AccessRole(StrEnum):
    OFFICIAL = "OFFICIAL"
    TRAINER = "TRAINER"
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"  # Legacy alias for backward compatibility


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
    access_role: AccessRole = Field(default=AccessRole.OFFICIAL)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_value(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("access_role", mode="before")
    @classmethod
    def normalize_access_role_value(cls, value: object) -> object:
        if isinstance(value, str):
            val_str = value.strip().upper()
            try:
                return AccessRole(val_str)
            except ValueError:
                return val_str
        return value

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

    # Extended profile fields (optional, present only if set)
    organization: str | None = None
    current_assignment: str | None = None
    years_experience: int | None = None
    service_year: int | None = None
    highest_qualification: str | None = None
    field_of_study: str | None = None
    institution: str | None = None
    graduation_year: int | None = None
    total_experience_summary: str | None = None
    key_responsibilities: str | None = None


class UserProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Core identity fields
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    designation: str | None = Field(default=None, min_length=1, max_length=200)
    department: str | None = Field(default=None, min_length=1, max_length=200)
    employee_id: str | None = Field(default=None, min_length=1, max_length=100)

    # Employment details
    organization: str | None = Field(default=None, max_length=300)
    current_assignment: str | None = Field(default=None, max_length=300)
    years_experience: int | None = Field(default=None, ge=0, le=50)
    service_year: int | None = Field(default=None, ge=1950, le=2030)

    # Education
    highest_qualification: str | None = Field(default=None, max_length=200)
    field_of_study: str | None = Field(default=None, max_length=200)
    institution: str | None = Field(default=None, max_length=300)
    graduation_year: int | None = Field(default=None, ge=1950, le=2030)

    # Professional summary
    total_experience_summary: str | None = Field(default=None, max_length=1000)
    key_responsibilities: str | None = Field(default=None, max_length=1000)

    @field_validator("full_name", "designation", "department", "employee_id",
                     "organization", "current_assignment", "highest_qualification",
                     "field_of_study", "institution", "total_experience_summary",
                     "key_responsibilities")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

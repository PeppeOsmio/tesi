from datetime import datetime
from uuid import UUID
from pydantic import EmailStr, Field
from tesi.schemas import CustomBaseModel


class UserDetailsResponse(CustomBaseModel):
    id: UUID
    username: str
    name: str
    created_at: datetime
    modified_at: datetime
    email: EmailStr | None
    is_active: bool


class UserCreateBody(CustomBaseModel):
    username: str = Field(max_length=255)
    name: str = Field(max_length=255)
    password: str = Field(max_length=255)
    email: EmailStr | None = Field(max_length=255)


class UsersCountResponse(CustomBaseModel):
    count: int

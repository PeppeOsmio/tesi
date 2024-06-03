from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field
from tesi.schemas import CustomBaseModel


class CreateAuthTokenBody(CustomBaseModel):
    username: str = Field(max_length=255)
    password: str = Field(max_length=255)


class AuthTokenDetailsResponse(CustomBaseModel):
    access_token: str
    token_type: Literal["bearer"]


class GetOwnInfoResponse(CustomBaseModel):
    id: UUID
    username: str
    name: str
    email: str | None
    created_at: datetime

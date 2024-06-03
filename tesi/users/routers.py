from typing import Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, Query
from fastapi.routing import APIRouter

from tesi.auth_tokens.di import get_current_user
from tesi.users.repositories.dtos import UserDTO
from tesi.users.repositories.exceptions import (
    EmailExistsError,
    UsernameExistsError,
)
from tesi.users.schemas import UserCreateBody, UserDetailsResponse
from tesi.users.repositories import UserRepository
from tesi.users.di import get_user_repository
from tesi.users.schemas import UsersCountResponse

user_router = APIRouter(prefix="/user")


@user_router.post(
    "/",
    response_model=UserDetailsResponse,
    responses={
        400: {
            "description": "Invalid data",
            "content": {"application/json": {"example": {"detail": "username_exists"}}},
        }
    },
)
async def create_user(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    data: UserCreateBody,
):
    try:
        user = await user_repository.create_user(
            username=data.username,
            password=data.password,
            name=data.name,
            email=data.email,
        )
        return UserDetailsResponse.model_construct(
            id=user.id,
            username=user.username,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
            modified_at=user.modified_at,
            is_active=user.is_active,
        )
    except UsernameExistsError:
        raise HTTPException(status_code=400, detail="username_exists")
    except EmailExistsError:
        raise HTTPException(status_code=400, detail="email_exists")


@user_router.get(
    "/{user_id}",
    response_model=UserDetailsResponse,
    responses={
        404: {
            "description": "User not found",
            "content": {"application/json": {"example": {"detail": "user_not_found"}}},
        }
    },
)
async def get_user_details(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    user_id: UUID,
):
    user = await user_repository.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="not_found")
    return UserDetailsResponse.model_construct(
        id=user.id,
        username=user.username,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
        modified_at=user.modified_at,
        is_active=user.is_active,
    )


@user_router.get("/", response_model=list[UserDetailsResponse])
async def get_users(
    _: Annotated[UserDTO | None, Depends(get_current_user)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    page_number: int = Query(default=1, ge=1),
    page_size: int = Query(default=1, ge=1),
):
    users = await user_repository.get_users(
        page_number=page_number, page_size=page_size
    )
    return [
        UserDetailsResponse.model_construct(
            id=user.id,
            username=user.username,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
            modified_at=user.modified_at,
            is_active=user.is_active,
        )
        for user in users
    ]


@user_router.get("/count", response_model=UsersCountResponse)
async def get_users_count(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)]
):
    count = await user_repository.get_users_count()
    return UsersCountResponse.model_construct(count=count)

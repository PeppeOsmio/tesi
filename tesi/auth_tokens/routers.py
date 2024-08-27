import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Header, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import async_sessionmaker
from tesi.auth_tokens.di import get_auth_token_repository, get_current_user
from tesi.auth_tokens.repositories import AuthTokenRepository
from tesi.auth_tokens.repositories.exceptions import WrongCredentialsError
from tesi.auth_tokens.schemas import (
    AuthTokenDetailsResponse,
    GetOwnInfoResponse,
)
from tesi.database.di import get_session_maker
from tesi.users.repositories.dtos import UserDTO
from tesi.users.models import User

auth_token_router = APIRouter(prefix="/auth")


@auth_token_router.post("/", response_model=AuthTokenDetailsResponse)
async def create_auth_token(
    session_maker: Annotated[async_sessionmaker, Depends(get_session_maker)],
    auth_token_repository: Annotated[
        AuthTokenRepository, Depends(get_auth_token_repository)
    ],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    user_agent: Annotated[str | None, Header()] = None,
):
    try:
        async with session_maker() as session:
            auth_token = await auth_token_repository.create_auth_token(
                session=session,
                username=form_data.username,
                password=form_data.password,
                user_agent=user_agent,
            )
        response.set_cookie(key="access_token", value=auth_token.token)
        return AuthTokenDetailsResponse(
            access_token=auth_token.token, token_type="bearer"
        )
    except WrongCredentialsError:
        raise HTTPException(status_code=401, detail="wrong_credentials")


@auth_token_router.get("/me", response_model=GetOwnInfoResponse)
async def get_own_info(user: Annotated[UserDTO | None, Depends(get_current_user)]):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return GetOwnInfoResponse(
        id=user.id,
        username=user.username,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
    )

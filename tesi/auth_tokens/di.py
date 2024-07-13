import logging
from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tesi.auth_tokens.repositories import AuthTokenRepository
from tesi.database.di import get_session_maker
from tesi.users.di import get_user_repository
from tesi.users.repositories.dtos import UserDTO
from tesi.users.models import User
from tesi.users.repositories.user_repository import UserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth", auto_error=False)


def get_auth_token_repository(
    db_session: Annotated[async_sessionmaker, Depends(get_session_maker)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthTokenRepository:
    return AuthTokenRepository(session_maker=db_session, user_repository=user_repository)


async def get_current_user(
    auth_token_repository: Annotated[
        AuthTokenRepository, Depends(get_auth_token_repository)
    ],
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> UserDTO | None:
    if token is None:
        return None
    return await auth_token_repository.get_user_from_auth_token(token)


async def get_current_user_with_error(
    user: Annotated[User, Depends(get_current_user)]
) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user

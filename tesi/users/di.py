from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from tesi.database.di import get_session_maker
from tesi.users.repositories import UserRepository


def get_user_repository(
    session_maker: Annotated[AsyncSession, Depends(get_db_session)]
) -> UserRepository:
    return UserRepository(db_session=db_session)

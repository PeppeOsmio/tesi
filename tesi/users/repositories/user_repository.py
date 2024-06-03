from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Literal
from uuid import UUID
import uuid

import bcrypt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count
from tesi.users.repositories.dtos import UserDTO
from tesi.users.models import User
from tesi.users.repositories.exceptions import (
    EmailExistsError,
    UserNotFoundError,
    UsernameExistsError,
)
from tesi.users.schemas import UserCreateBody


class UserRepository:

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def get_user_by_id(self, user_id: UUID) -> UserDTO | None:
        """

        Args:
            user_id (UUID):

        Returns:
            User | None:
        """
        async with self.db_session as session:
            stmt = select(User).where(User.id == user_id)
            user = await session.scalar(stmt)
        if user is None:
            return None
        return UserDTO(
            id=user.id,
            username=user.username,
            name=user.name,
            created_at=user.created_at,
            modified_at=user.modified_at,
            email=user.email,
            is_active=user.is_active,
        )

    async def get_users(self, page_number: int, page_size: int) -> list[UserDTO]:
        """Get users with pagination and page size.

        Args:
            cursor (str):
            page_size (int):

        Returns:
            list[User]:
        """
        async with self.db_session as session:
            stmt = (
                select(User)
                .order_by(User.created_at, User.id)
                .offset((page_number - 1) * page_size)
                .limit(page_size)
            )
            results = await session.scalars(stmt)
        return [
            UserDTO(
                id=user.id,
                username=user.username,
                name=user.name,
                created_at=user.created_at,
                modified_at=user.modified_at,
                email=user.email,
                is_active=user.is_active,
            )
            for user in results
        ]

    async def get_users_count(self) -> int:
        """

        Raises:
            Exception:

        Returns:
            int:
        """
        async with self.db_session as session:
            stmt = select(count(User.id))
            result = await session.scalar(stmt)
        if result is None:
            raise Exception("idk why count is none")
        return result

    async def create_user(
        self, username: str, password: str, name: str, email: str | None
    ) -> UserDTO:
        async with self.db_session as session:
            exists_username_stmt = select(User.id).where(User.username == username)
            user_id = await session.scalar(exists_username_stmt)
            if user_id is not None:
                raise UsernameExistsError()
            exists_email_stmt = select(User.email).where(User.email == email)
            email = await session.scalar(exists_email_stmt)
            if email is not None:
                raise EmailExistsError()
            now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
            user = User(
                id=uuid.uuid4(),
                username=username,
                name=name,
                email=email,
                password=self.__hash_password(password),
                created_at=now,
                modified_at=now,
                is_active=True,
            )
            session.add(user)
            await session.commit()
        return UserDTO(
            id=user.id,
            username=user.username,
            name=user.name,
            created_at=user.created_at,
            modified_at=user.modified_at,
            email=user.email,
            is_active=user.is_active,
        )

    async def check_password(self, username: str, password: str) -> bool:
        async with self.db_session as session:
            stmt = select(User.password).where(User.username == username)
            hashed_pw = await session.scalar(stmt)
            if hashed_pw is None:
                raise UserNotFoundError()
            return bcrypt.checkpw(
                password=password.encode(), hashed_password=hashed_pw.encode()
            )

    async def get_user_id_from_username(self, username: str) -> UUID | None:
        async with self.db_session as session:
            stmt = select(User.id).where(User.username == username)
            result = (await session.execute(stmt)).first()
        if result is None:
            return None
        return result.tuple()[0]

    async def check_user_exists(self, user_id: UUID) -> bool:
        async with self.db_session as session:
            stmt = select(User.id).where(User.id == user_id)
            result = await session.execute(stmt)
        return result.first() is None

    def __hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt()).decode()

    async def check_is_admin(self, executor_id: UUID) -> bool | None:
        """Check if a user is an admin.

        Args:
            executor_id (UUID):

        Returns:
            bool | None: whether the user is an admin or None if the user does not exist.
        """
        async with self.db_session as session:
            stmt = select(User.is_admin).where(User.id == executor_id)
            is_admin = await session.scalar(stmt)
        return is_admin

    async def deactivate_user(
        self, user_id: UUID, executor_id: UUID
    ) -> Literal[True] | None:
        """Deactivate a user.

        Args:
            user_id (UUID): the user to deactivate
            executor_id (UUID): the user executing this function

        Raises:
            PermissionError:

        Returns:
            Literal[True] | None: True if the user was found and deactivated, otherwise None
        """
        is_admin = await self.check_is_admin(executor_id)
        if is_admin is None:
            raise PermissionError()
        if not is_admin:
            raise PermissionError()
        async with self.db_session as session:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(is_active=False)
                .returning(User.id)
            )
            result = (await session.execute(stmt)).first()
        if result is None:
            return None
        return None

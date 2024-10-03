import argparse
import asyncio
import logging

from zappai import logging_conf
from zappai.auth_tokens.di import get_auth_token_repository
from zappai.database.di import get_session_maker
from zappai.users.di import get_user_repository
from zappai.users.repositories.exceptions import UserNotFoundError

async def main():
    # Create the ArgumentParser object
    parser = argparse.ArgumentParser(
        description="Logout a user from everywhere"
    )

    # Add the file path argument
    parser.add_argument("--username", type=str, required=True)

    args = parser.parse_args()

    user_repository = get_user_repository()
    auth_token_repository = get_auth_token_repository(user_repository=user_repository)
    session_maker = get_session_maker()

    async with session_maker() as session:
        await user_repository.delete_user(session=session, username=args.username)
        user_id = await user_repository.get_user_id_from_username(session=session, username=args.username)
        if user_id is None:
            raise UserNotFoundError(username=args.username)
        await auth_token_repository.revoke_all_tokens(session=session, user_id=user_id)
        await session.commit()
    
    print(f"User {args.username} logged out from everywhere!")

if __name__ == "__main__":
    logging_conf.create_logger(config=logging_conf.get_default_conf())
    asyncio.run(main())
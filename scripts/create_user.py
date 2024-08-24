import argparse
import asyncio

from tesi.database.di import get_session_maker
from tesi.users.di import get_user_repository

async def main():
    # Create the ArgumentParser object
    parser = argparse.ArgumentParser(
        description="Create the admin user"
    )

    # Add the file path argument
    parser.add_argument("--username", type=str)
    parser.add_argument("--password", type=str)
    parser.add_argument("--name", type=str)
    parser.add_argument("--email", type=str)

    args = parser.parse_args()

    user_repository = get_user_repository()
    session_maker = get_session_maker()

    async with session_maker() as session:
        await user_repository.create_user(session=session, username=args.username, password=args.password, name=args.name, email=args.email)
        await session.commit()

if __name__ == "__main__":
    asyncio.run(main())
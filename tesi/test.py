import asyncio
import random


async def coro(number: int):
    for _ in range(random.randint(10, 30)):
        await asyncio.sleep(random.randint(2, 10))
        print(f"Hello from {number}")


async def main():
    await asyncio.gather(coro(1), coro(2), coro(3), coro(4), coro(5))


if __name__ == "__main__":
    asyncio.run(main())

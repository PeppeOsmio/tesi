from contextlib import asynccontextmanager
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.middleware.cors import CORSMiddleware
from tesi import logging_conf
from tesi.database.di import get_session_maker
from tesi.zappai.di import get_location_repository
from tesi.zappai.repositories.location_repository import LocationRepository

logging_conf.create_logger(config=logging_conf.get_default_conf())

import logging
import traceback
from fastapi import Depends, FastAPI, Request
from starlette.responses import JSONResponse

from tesi.users.routers import user_router
from tesi.auth_tokens.routers import auth_token_router
from tesi.zappai.routers import zappai_router


@asynccontextmanager
async def lifespan(
    app: FastAPI
):
    session_maker = get_session_maker()
    location_repository = get_location_repository()
    async with session_maker() as session:
        await location_repository.set_locations_to_not_downloading(session=session)
        await session.commit()
    logging.info("Done")
    yield


app = FastAPI(lifespan=lifespan)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user_router, prefix="/api", tags=["User"])
app.include_router(auth_token_router, prefix="", tags=["Auth"])
app.include_router(zappai_router, prefix="/api", tags=["Zappai"])


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"type": type(exc).__qualname__, "detail": str(exc)},
    )

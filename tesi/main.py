import tesi.logging_conf
import logging
import traceback
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from tesi.users.routers import user_router
from tesi.auth_tokens.routers import auth_token_router
from tesi.zappai.routers import zappai_router

app = FastAPI()

app.include_router(user_router, prefix="/api", tags=["User"])
app.include_router(auth_token_router, prefix="/api", tags=["Auth"])
app.include_router(zappai_router, prefix="/api", tags=["Zappai"])


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"type": type(exc).__qualname__, "detail": str(exc)},
    )

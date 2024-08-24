from fastapi.routing import APIRouter
from tesi.zappai.routers.crops_router import crops_router
from tesi.zappai.routers.predictions_router import predictions_router
from tesi.zappai.routers.locations_router import locations_router

zappai_router = APIRouter(prefix="")
zappai_router.include_router(crops_router)
zappai_router.include_router(predictions_router)
zappai_router.include_router(locations_router)

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import async_sessionmaker

from tesi.auth_tokens.di import get_current_user
from tesi.database.di import get_session_maker
from tesi.users.models import User
from tesi.zappai.di import get_crop_optimizer_service
from tesi.zappai.exceptions import ClimateGenerativeModelNotFoundError, CropYieldModelNotFoundError
from tesi.zappai.schemas import PredictionsResponse
from tesi.zappai.services.crop_optimizer_service import CropOptimizerService

predictions_router = APIRouter(prefix="/predictions")

@predictions_router.get(path="")
async def get_best_crop_sowing_and_harvesting_prediction(
    user: Annotated[User, Depends(get_current_user)],
    session_maker: Annotated[async_sessionmaker, Depends(get_session_maker)],
    crop_optimizer_service: Annotated[CropOptimizerService, Depends(get_crop_optimizer_service)],
    crop_id: UUID,
    location_id: UUID,
    response: Response
):
    try:
        async with session_maker() as session:
            result = await crop_optimizer_service.get_best_crop_sowing_and_harvesting(session=session, crop_id=crop_id, location_id=location_id)
        return PredictionsResponse(
            best_combinations=result.best_combinations,
            forecast=result.forecast
        )
    except CropYieldModelNotFoundError:
        response.status_code = 404
        return {
            "error": "crop_yield_model_not_found"
        }
    except ClimateGenerativeModelNotFoundError:
        return {
            "error": "climate_generative_model_not_found"
        }

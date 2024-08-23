from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import async_sessionmaker

from tesi.database.di import get_session_maker
from tesi.zappai.di import get_past_climate_data_repository
from tesi.zappai.repositories.past_climate_data_repository import (
    PastClimateDataRepository,
)
from tesi.zappai.schemas import GetPastClimateDataOfLocationResponse


past_climate_data_router = APIRouter(prefix="/past_climate_data")


@past_climate_data_router.get(
    "/{location_id}", response_model=list[GetPastClimateDataOfLocationResponse]
)
async def get_past_climate_data_of_location(
    session_maker: Annotated[async_sessionmaker, get_session_maker],
    location_id: UUID,
    year_from: int,
    year_to: int,
    past_climate_data_repository: Annotated[
        PastClimateDataRepository, Depends(get_past_climate_data_repository)
    ],
):
    async with session_maker() as session:
        data = await past_climate_data_repository.get_past_climate_data(session=session, location_id=location_id, year_from=year_from, year_to=year_to)
        result = [
            GetPastClimateDataOfLocationResponse(
                year=item.year,
                month=item.month,
                temperature_2m=item.
            )
            for item in data
        ]

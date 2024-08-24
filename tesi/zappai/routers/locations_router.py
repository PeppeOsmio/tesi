from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from sqlalchemy.ext.asyncio import async_sessionmaker

from tesi.auth_tokens.di import get_current_user
from tesi.database.di import get_session_maker
from uuid import UUID

from tesi.users.models import User
from tesi.zappai.di import get_location_repository, get_past_climate_data_repository
from tesi.zappai.repositories.location_repository import LocationRepository
from tesi.zappai.repositories.past_climate_data_repository import (
    PastClimateDataRepository,
)
from tesi.zappai.schemas import CreateLocationBody, LocationDetailsResponse


locations_router = APIRouter(prefix="/locations")


@locations_router.post(path="", response_model=LocationDetailsResponse)
async def create_location(
    user: Annotated[User, Depends(get_current_user)],
    session_maker: Annotated[async_sessionmaker, Depends(get_session_maker)],
    location_repository: Annotated[
        LocationRepository, Depends(get_location_repository)
    ],
    data: CreateLocationBody,
):
    async with session_maker() as session:
        location = await location_repository.create_location(
            session=session,
            country=data.country,
            name=data.name,
            longitude=data.longitude,
            latitude=data.latitude,
        )
        await session.commit()
    return LocationDetailsResponse(
        id=location.id,
        country=location.country,
        name=location.name,
        latitude=location.latitude,
        longitude=location.longitude,
        last_past_climate_data_year=None,
        last_past_climate_data_month=None,
    )


@locations_router.get(path="/", response_model=list[LocationDetailsResponse])
async def get_locations(
    user: Annotated[User, Depends(get_current_user)],
    session_maker: Annotated[async_sessionmaker, Depends(get_session_maker)],
    location_repository: Annotated[
        LocationRepository, Depends(get_location_repository)
    ],
    past_climate_data_repository: Annotated[
        PastClimateDataRepository, Depends(get_past_climate_data_repository)
    ],
) -> list[LocationDetailsResponse]:
    async with session_maker() as session:
        result = await location_repository.get_locations(session=session)
        response: list[LocationDetailsResponse] = []
        for location in result:
            data = await past_climate_data_repository.get_past_climate_data_of_previous_n_months(
                session=session, location_id=location.id, n=1
            )
            year = None if len(data) == 0 else data[0].year
            month = None if len(data) == 0 else data[0].month
            response.append(
                LocationDetailsResponse(
                    id=location.id,
                    country=location.country,
                    name=location.name,
                    longitude=location.longitude,
                    latitude=location.latitude,
                    last_past_climate_data_year=year,
                    last_past_climate_data_month=month,
                )
            )
    return response


@locations_router.delete(path="/{location_id}")
async def delete_location(
    user: Annotated[User, Depends(get_current_user)],
    session_maker: Annotated[async_sessionmaker, Depends(get_session_maker)],
    location_repository: Annotated[
        LocationRepository, Depends(get_location_repository)
    ],
    location_id: UUID,
):
    async with session_maker() as session:
        await location_repository.delete_location(
            session=session, location_id=location_id
        )
        await session.commit()


@locations_router.post(path="/past_climate_data/{location_id}")
async def download_past_climate_data_for_location(
    user: Annotated[User, Depends(get_current_user)],
    session_maker: Annotated[async_sessionmaker, Depends(get_session_maker)],
    past_climate_data_repository: Annotated[
        PastClimateDataRepository, Depends(get_past_climate_data_repository)
    ],
    location_id: UUID,
    background_tasks: BackgroundTasks,
):
    async def func():
        async with session_maker() as session:
            await past_climate_data_repository.download_new_past_climate_data(
                session=session, location_id=location_id
            )
            await session.commit()

    background_tasks.add_task(func=func)
    return {"message": "Download started"}

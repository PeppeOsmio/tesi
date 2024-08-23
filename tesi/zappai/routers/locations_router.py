from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import async_sessionmaker

from tesi.database.di import get_session_maker
from uuid import UUID

from tesi.zappai.di import get_location_repository, get_past_climate_data_repository
from tesi.zappai.repositories.location_repository import LocationRepository
from tesi.zappai.repositories.past_climate_data_repository import (
    PastClimateDataRepository,
)
from tesi.zappai.schemas import CreateLocationBody, LocationDetailsResponse


locations_router = APIRouter(prefix="/locations")


@locations_router.post(path="/locations", response_model=LocationDetailsResponse)
async def create_location(
    session_maker: Annotated[async_sessionmaker, get_session_maker],
    location_repository: Annotated[LocationRepository, get_location_repository],
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
    return location


@locations_router.get(path="/locations", response_model=list[LocationDetailsResponse])
async def get_locations(
    session_maker: Annotated[async_sessionmaker, Depends(get_session_maker)],
    location_repository: Annotated[
        LocationRepository, Depends(get_location_repository)
    ],
):
    async with session_maker() as session:
        result = await location_repository.get_locations(session=session)
    return result


@locations_router.delete(path="/locations/{location_id}")
async def delete_location(
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

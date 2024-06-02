from typing import Annotated
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from fastapi import Depends

from tesi.climate.repositories.crop_repository import CropRepository
from tesi.climate.repositories.crop_yield_data_repository import CropYieldDataRepository
from tesi.climate.repositories.future_climate_data_repository import (
    FutureClimateDataRepository,
)
from tesi.climate.repositories.location_repository import LocationRepository
from tesi.climate.repositories.past_climate_data_repository import (
    PastClimateDataRepository,
)
from tesi.climate.repositories.copernicus_data_store_api import CopernicusDataStoreAPI
from tesi.database.di import get_session_maker


def get_location_repository(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)],
) -> LocationRepository:
    return LocationRepository(session_maker=session_maker)


def get_crop_repository(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)],
) -> CropRepository:
    return CropRepository(session_maker=session_maker)


def get_crop_yield_data_repository(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)],
    crop_repository: Annotated[CropRepository, Depends(get_crop_repository)],
    location_repository: Annotated[
        LocationRepository, Depends(get_location_repository)
    ],
) -> CropYieldDataRepository:
    return CropYieldDataRepository(
        session_maker=session_maker,
        crop_repository=crop_repository,
        location_repository=location_repository,
    )


def get_cds_api() -> CopernicusDataStoreAPI:
    return CopernicusDataStoreAPI(
        user_id=311032, api_token=UUID(hex="15a4dd58-d44c-4d52-afa3-db18f38e1d2c")
    )


def get_past_climate_data_repository(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)],
    cds_api: Annotated[CopernicusDataStoreAPI, get_cds_api],
    location_repository: Annotated[LocationRepository, get_location_repository],
) -> PastClimateDataRepository:
    return PastClimateDataRepository(
        session_maker=session_maker,
        copernicus_data_store_api=cds_api,
        location_repository=location_repository,
    )


def get_future_climate_data_repository(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)],
    cds_api: Annotated[CopernicusDataStoreAPI, get_cds_api],
) -> FutureClimateDataRepository:
    return FutureClimateDataRepository(
        session_maker=session_maker, copernicus_data_store_api=cds_api
    )

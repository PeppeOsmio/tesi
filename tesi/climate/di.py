from typing import Annotated
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
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
from tesi.climate.utils.copernicus_data_store_api import CopernicusDataStoreAPI
from tesi.database.di import get_db_session


def get_location_repository(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> LocationRepository:
    return LocationRepository(db_session=db_session)


def get_crop_repository(
    db_session: Annotated[AsyncSession, Depends(get_db_session)]
) -> CropRepository:
    return CropRepository(db_session=db_session)


def get_crop_yield_data_repository(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    crop_repository: Annotated[CropRepository, Depends(get_crop_repository)],
    location_repository: Annotated[
        LocationRepository, Depends(get_location_repository)
    ],
) -> CropYieldDataRepository:
    return CropYieldDataRepository(
        db_session=db_session,
        crop_repository=crop_repository,
        location_repository=location_repository,
    )


def get_cds_api() -> CopernicusDataStoreAPI:
    return CopernicusDataStoreAPI(
        user_id=311032, api_token=UUID(hex="15a4dd58-d44c-4d52-afa3-db18f38e1d2c")
    )


def get_past_climate_data_repository(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    cds_api: Annotated[CopernicusDataStoreAPI, get_cds_api],
    location_repository: Annotated[LocationRepository, get_location_repository],
) -> PastClimateDataRepository:
    return PastClimateDataRepository(
        db_session=db_session,
        copernicus_data_store_api=cds_api,
        location_repository=location_repository,
    )


def get_future_climate_data_repository(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    cds_api: Annotated[CopernicusDataStoreAPI, get_cds_api],
) -> FutureClimateDataRepository:
    return FutureClimateDataRepository(
        db_session=db_session, copernicus_data_store_api=cds_api
    )

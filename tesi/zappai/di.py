from typing import Annotated
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from fastapi import Depends

from tesi.zappai.repositories.climate_generative_model_repository import (
    ClimateGenerativeModelRepository,
)
from tesi.zappai.repositories.crop_repository import CropRepository
from tesi.zappai.repositories.crop_yield_data_repository import CropYieldDataRepository
from tesi.zappai.services.crop_yield_model_service import (
    CropYieldModelService,
)
from tesi.zappai.repositories.future_climate_data_repository import (
    FutureClimateDataRepository,
)
from tesi.zappai.repositories.location_repository import LocationRepository
from tesi.zappai.repositories.past_climate_data_repository import (
    PastClimateDataRepository,
)
from tesi.zappai.repositories.copernicus_data_store_api import CopernicusDataStoreAPI
from tesi.database.di import get_session_maker


def get_location_repository(
    session_maker: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_session_maker)
    ],
) -> LocationRepository:
    return LocationRepository(session_maker=session_maker)


def get_crop_repository(
    session_maker: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_session_maker)
    ],
) -> CropRepository:
    return CropRepository(session_maker=session_maker)


def get_cds_api() -> CopernicusDataStoreAPI:
    return CopernicusDataStoreAPI(
        user_id=311032, api_token=UUID(hex="15a4dd58-d44c-4d52-afa3-db18f38e1d2c")
    )


def get_past_climate_data_repository(
    session_maker: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_session_maker)
    ],
    cds_api: Annotated[CopernicusDataStoreAPI, Depends(get_cds_api)],
    location_repository: Annotated[
        LocationRepository, Depends(get_location_repository)
    ],
) -> PastClimateDataRepository:
    return PastClimateDataRepository(
        session_maker=session_maker,
        copernicus_data_store_api=cds_api,
        location_repository=location_repository,
    )


def get_crop_yield_data_repository(
    crop_repository: Annotated[CropRepository, Depends(get_crop_repository)],
    location_repository: Annotated[
        LocationRepository, Depends(get_location_repository)
    ],
    past_climate_data_repository: Annotated[
        PastClimateDataRepository, Depends(get_past_climate_data_repository)
    ],
) -> CropYieldDataRepository:
    return CropYieldDataRepository(
        crop_repository=crop_repository,
        location_repository=location_repository,
        past_climate_data_repository=past_climate_data_repository,
    )


def get_future_climate_data_repository(
    session_maker: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_session_maker)
    ],
    cds_api: Annotated[CopernicusDataStoreAPI, Depends(get_cds_api)],
) -> FutureClimateDataRepository:
    return FutureClimateDataRepository(
        session_maker=session_maker, copernicus_data_store_api=cds_api
    )


def get_climate_generative_model_repository(
    session_maker: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_session_maker)
    ],
    location_repository: Annotated[
        LocationRepository, Depends(get_location_repository)
    ],
    past_climate_data_repository: Annotated[
        PastClimateDataRepository, Depends(get_past_climate_data_repository)
    ],
    future_climate_data_repository: Annotated[
        FutureClimateDataRepository, Depends(get_future_climate_data_repository)
    ],
) -> ClimateGenerativeModelRepository:
    return ClimateGenerativeModelRepository(
        session_maker=session_maker,
        location_repository=location_repository,
        past_climate_data_repository=past_climate_data_repository,
        future_climate_data_repository=future_climate_data_repository,
    )


def get_crop_yield_model_service(
    past_climate_data_repository: Annotated[
        PastClimateDataRepository, Depends(get_past_climate_data_repository)
    ],
    location_repository: Annotated[
        LocationRepository, Depends(get_location_repository)
    ],
    crop_yield_data_repository: Annotated[
        CropYieldDataRepository, Depends(get_crop_yield_data_repository)
    ],
    crop_repository: Annotated[CropRepository, Depends(get_crop_repository)],
) -> CropYieldModelService:
    return CropYieldModelService(
        past_climate_data_repository=past_climate_data_repository,
        location_repository=location_repository,
        crop_yield_data_repository=crop_yield_data_repository,
        crop_repository=crop_repository,
    )

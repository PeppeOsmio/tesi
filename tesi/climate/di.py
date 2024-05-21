from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from tesi.climate.repositories.future_climate_data_repository import (
    FutureClimateDataRepository,
)
from tesi.database.di import get_db_session


def get_future_climate_data_repository(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    training_data_folder: str,
) -> FutureClimateDataRepository:
    return FutureClimateDataRepository(
        db_session=db_session, training_data_folder=training_data_folder
    )

def get_future_climate_data_repository(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    training_data_folder: str,
) -> FutureClimateDataRepository:
    return FutureClimateDataRepository(
        db_session=db_session, training_data_folder=training_data_folder
    )

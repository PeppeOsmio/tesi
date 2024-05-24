import pandas as pd
from asgiref.sync import sync_to_async
from tesi.climate.repositories.dtos import PastClimateDataDTO
from tesi.climate.utils.copernicus_data_store_api import CopernicusDataStoreAPI
from sqlalchemy.ext.asyncio import AsyncSession


class PastClimateDataRepository:
    def __init__(
        self,
        db_session: AsyncSession,
        copernicus_data_store_api: CopernicusDataStoreAPI,
    ) -> None:
        self.copernicus_data_store_api = copernicus_data_store_api
        self.db_session = db_session

    def get_past_climate_data(self, longitude: float, latitude: float) -> pd.DataFrame:
        return self.copernicus_data_store_api.get_past_climate_data_since_1940(
            longitude=longitude, latitude=latitude
        )

    def get_past_climate_data_of_last_12_months(
        self, longitude: float, latitude: float
    ) -> pd.DataFrame:
        return self.copernicus_data_store_api.get_climate_data_of_last_12_months(
            longitude=longitude, latitude=latitude
        )

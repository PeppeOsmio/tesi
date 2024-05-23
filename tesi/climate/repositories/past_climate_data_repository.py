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

    @sync_to_async
    def get_past_climate_data(
        self, longitude: float, latitude: float
    ) -> list[PastClimateDataDTO]:
        df = self.copernicus_data_store_api.get_past_climate_data_since_1940(
            longitude=longitude, latitude=latitude
        )
        result: list[PastClimateDataDTO] = []
        for i, row in df.iterrows():
            result.append(
                PastClimateDataDTO(
                    year=row["year"],
                    month=row["month"],
                    longitude=row["longitude"],
                    latitude=row["latitude"],
                    total_precipitations=row["total_precipitations"],
                    surface_temperature=row["surface_temperature"],
                    surface_net_solar_radiation=row["surface_net_solar_radiation"],
                    surface_pressure=row["surface_pressure"],
                )
            )

    @sync_to_async
    def get_past_climate_data_of_last_12_months(
        self, longitude: float, latitude: float
    ) -> pd.DataFrame:
        return self.copernicus_data_store_api.get_climate_data_of_last_12_months(
            longitude=longitude, latitude=latitude
        )

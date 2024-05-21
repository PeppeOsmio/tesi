import logging
import os
from geoalchemy2 import Geography
import pandas as pd
from asgiref.sync import sync_to_async
from sqlalchemy import select
from tesi.climate.dtos import FutureClimateDataDTO
from tesi.climate.models import FutureClimateData
from tesi.climate.utils.copernicus_data_store_api import CopernicusDataStoreAPI
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_X, ST_Y, ST_DistanceSphere


class PastClimateDataRepository:
    def __init__(self, db_session: AsyncSession, copernicus_data_store_api: CopernicusDataStoreAPI) -> None:
        self.copernicus_data_store_api = copernicus_data_store_api
        self.db_session = db_session

    @sync_to_async
    def get_past_climate_data(self, longitude: float, latitude: float) -> pd.DataFrame:
        return self.copernicus_data_store_api.get_past_climate_data_since_1940(longitude=longitude,latitude=latitude)

    @sync_to_async
    def get_past_climate_data_of_last_12_months(self, longitude: float, latitude: float) -> pd.DataFrame:
        return self.copernicus_data_store_api.get_climate_data_of_last_12_months(longitude=longitude, latitude=latitude)


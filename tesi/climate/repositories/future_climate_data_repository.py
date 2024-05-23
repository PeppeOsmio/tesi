import os
import pandas as pd
from asgiref.sync import sync_to_async
from sqlalchemy import delete, select
from tesi.climate.dtos import FutureClimateDataDTO
from tesi.climate.models import FutureClimateData
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_X, ST_Y, ST_DistanceSphere

from tesi.climate.utils.copernicus_data_store_api import CopernicusDataStoreAPI


class FutureClimateDataRepository:
    def __init__(
        self,
        db_session: AsyncSession,
        training_data_folder: str,
        copernicus_data_store_api: CopernicusDataStoreAPI,
    ) -> None:
        self.db_session = db_session
        self.training_data_folder = training_data_folder
        self.copernicus_data_store_api = copernicus_data_store_api

    async def download_future_climate_data_into_db(self):

        @sync_to_async
        def func():
            return self.copernicus_data_store_api.download_future_climate_data()

        future_climate_df = await func()
        async with self.db_session as session:
            stmt = delete(FutureClimateData)
            await session.execute(stmt)
            processed = 0
            STEP = 100
            total = len(future_climate_df)
            while processed < total:
                rows = future_climate_df[processed : processed + STEP]
                for i, row in rows.iterrows():
                    future_climate_data = FutureClimateData(
                        coordinates=f'POINT({row["longitude"], row["latitude"]})',
                        year=row["year"],
                        month=row["month"],
                        precipitations=row["precipitations"],
                        surface_temperature=row["surface_temperature"],
                    )
                    session.add(future_climate_data)
                processed += len(rows)
            await session.commit()

    async def get_future_climate_data_for_coordinates(
        self, latitude: float, longitude: float
    ) -> FutureClimateDataDTO:
        point_well_known_text = f"POINT({longitude} {latitude})"
        async with self.db_session as session:
            stmt = (
                select(
                    FutureClimateData,
                    ST_X(FutureClimateData.coordinates).label("longitude"),
                    ST_Y(FutureClimateData.coordinates).label("latitude"),
                )
                .order_by(
                    ST_DistanceSphere(
                        FutureClimateData.coordinates, point_well_known_text
                    )
                )
                .limit(1)
            )
            result = (await session.execute(stmt)).first()
        if result is None:
            raise Exception(f"Can't find")
        future_climate_data, longitude, latitude = result.tuple()
        return FutureClimateDataDTO(
            year=future_climate_data.year,
            month=future_climate_data.month,
            latitude=latitude,
            longitude=longitude,
            precipitations=future_climate_data.precipitations,
            surface_temperature=future_climate_data.surface_temperature,
        )

import os
import pandas as pd
from asgiref.sync import async_to_sync, sync_to_async
from sqlalchemy import delete, select
from tesi.climate.dtos import FutureClimateDataDTO
from tesi.climate.models import FutureClimateData
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_X, ST_Y, ST_DistanceSphere
from typing import cast
from tesi.climate.utils.copernicus_data_store_api import CopernicusDataStoreAPI


class FutureClimateDataRepository:
    def __init__(
        self,
        db_session: AsyncSession,
        copernicus_data_store_api: CopernicusDataStoreAPI,
    ) -> None:
        self.db_session = db_session
        self.copernicus_data_store_api = copernicus_data_store_api

    @staticmethod
    def coordinates_to_well_known_text(longitude: float, latitude: float) -> str:
        return f"POINT({longitude} {latitude})"

    def download_future_climate_data(self) -> pd.DataFrame:
        return self.copernicus_data_store_api.download_future_climate_data()

    def save_future_climate_data(self, future_climate_data_df: pd.DataFrame):

        @async_to_sync
        async def save_in_db(future_climate_data_df: pd.DataFrame):
            async with self.db_session as session:
                stmt = delete(FutureClimateData)
                await session.execute(stmt)
                processed = 0
                STEP = 50
                total = len(future_climate_data_df)
                while processed < total:
                    rows = future_climate_data_df[processed : processed + STEP]
                    print(len(rows))
                    for index, row in rows.iterrows():
                        index = cast(pd.MultiIndex, index)
                        year, month = index
                        coordinates_wkt = (
                            FutureClimateDataRepository.coordinates_to_well_known_text(
                                longitude=row["longitude"], latitude=row["latitude"]
                            )
                        )
                        print(coordinates_wkt)
                        future_climate_data = FutureClimateData(
                            coordinates_str=coordinates_wkt,
                            coordinates=coordinates_wkt,
                            year=year,
                            month=month,
                            u_component_of_wind_10m=row["10m_u_component_of_wind"],
                            v_component_of_wind_10m=row["10m_v_component_of_wind"],
                            temperature_2m=row["2m_temperature"],
                            evaporation=row["evaporation"],
                            total_precipitation=row["total_precipitation"],
                            surface_pressure=row["surface_pressure"],
                            surface_solar_radiation_downwards=row[
                                "surface_solar_radiation_downwards"
                            ],
                            surface_thermal_radiation_downwards=row[
                                "surface_thermal_radiation_downwards"
                            ],
                        )
                        session.add(future_climate_data)
                    processed += len(rows)
                    await session.commit()

        save_in_db(future_climate_data_df)

    @async_to_sync
    async def get_future_climate_data_for_coordinates(
        self, longitude: float, latitude: float
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
            longitude=longitude,
            latitude=latitude,
            u_component_of_wind_10m=future_climate_data.u_component_of_wind_10m,
            v_component_of_wind_10m=future_climate_data.v_component_of_wind_10m,
            temperature_2m=future_climate_data.temperature_2m,
            evaporation=future_climate_data.evaporation,
            total_precipitation=future_climate_data.total_precipitation,
            surface_pressure=future_climate_data.surface_pressure,
            surface_solar_radiation_downwards=future_climate_data.surface_solar_radiation_downwards,
            surface_thermal_radiation_downwards=future_climate_data.surface_thermal_radiation_downwards,
        )

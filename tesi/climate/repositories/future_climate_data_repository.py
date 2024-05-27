import asyncio
from concurrent.futures import ThreadPoolExecutor
from geoalchemy2 import Geography
import pandas as pd
from sqlalchemy import delete, select
from tesi.climate.dtos import FutureClimateDataDTO
from tesi.climate.models import FutureClimateData
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_Distance
from typing import cast
import sqlalchemy
from tesi.climate.utils.common import coordinates_to_well_known_text
from tesi.climate.utils.copernicus_data_store_api import CopernicusDataStoreAPI


class FutureClimateDataRepository:
    def __init__(
        self,
        db_session: AsyncSession,
        copernicus_data_store_api: CopernicusDataStoreAPI,
    ) -> None:
        self.db_session = db_session
        self.copernicus_data_store_api = copernicus_data_store_api

    async def download_future_climate_data(self) -> pd.DataFrame:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(
                executor=pool,
                func=lambda: self.copernicus_data_store_api.get_future_climate_data(),
            )
        return result

    async def did_download_future_climate_data(self) -> bool:
        async with self.db_session as session:
            stmt = select(FutureClimateData.year).limit(1)
            result = await session.scalar(stmt)
        return result is not None

    async def save_future_climate_data(self, future_climate_data_df: pd.DataFrame):

        async with self.db_session as session:
            stmt = delete(FutureClimateData)
            await session.execute(stmt)
            processed = 0
            STEP = 50
            total = len(future_climate_data_df)
            while processed < total:
                rows = future_climate_data_df[processed : processed + STEP]
                for index, row in rows.iterrows():
                    index = cast(pd.MultiIndex, index)
                    year, month = index
                    coordinates_wkt = coordinates_to_well_known_text(
                        longitude=row["longitude"], latitude=row["latitude"]
                    )
                    future_climate_data = FutureClimateData(
                        longitude=row["longitude"],
                        latitude=row["latitude"],
                        year=year,
                        month=month,
                        coordinates=coordinates_wkt,
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

    async def get_future_climate_data_for_coordinates(
        self, longitude: float, latitude: float
    ) -> list[FutureClimateDataDTO]:
        point_well_known_text = f"POINT({longitude} {latitude})"
        async with self.db_session as session:
            stmt = (
                select(
                    FutureClimateData,
                )
                .order_by(
                    ST_Distance(
                        FutureClimateData.coordinates, sqlalchemy.cast(point_well_known_text, Geography)
                    )
                )
                .limit(1)
            )
            results = list(await session.scalars(stmt))
        if len(results) is None:
            raise Exception(
                f"Can't find future climate data for {longitude} {latitude}"
            )
        return self.__future_climate_data_models_to_dtos(results)

    def __future_climate_data_models_to_dtos(
        self, lst: list[FutureClimateData]
    ) -> list[FutureClimateDataDTO]:
        future_climate_data_list: list[FutureClimateDataDTO] = []
        for future_climate_data in lst:
            future_climate_data_list.append(
                FutureClimateDataDTO(
                    year=future_climate_data.year,
                    month=future_climate_data.month,
                    longitude=future_climate_data.longitude,
                    latitude=future_climate_data.latitude,
                    u_component_of_wind_10m=future_climate_data.u_component_of_wind_10m,
                    v_component_of_wind_10m=future_climate_data.v_component_of_wind_10m,
                    temperature_2m=future_climate_data.temperature_2m,
                    evaporation=future_climate_data.evaporation,
                    total_precipitation=future_climate_data.total_precipitation,
                    surface_pressure=future_climate_data.surface_pressure,
                    surface_solar_radiation_downwards=future_climate_data.surface_solar_radiation_downwards,
                    surface_thermal_radiation_downwards=future_climate_data.surface_thermal_radiation_downwards,
                )
            )
        return future_climate_data_list

import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import uuid
from geoalchemy2 import Geography
import pandas as pd
from sqlalchemy import asc, delete, func, insert, select
from tesi.climate.dtos import FutureClimateDataDTO
from tesi.climate.models import FutureClimateData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from geoalchemy2.functions import ST_Distance
from typing import Any, cast
import sqlalchemy
from tesi.climate.utils.common import coordinates_to_well_known_text
from tesi.climate.repositories.copernicus_data_store_api import CopernicusDataStoreAPI


class FutureClimateDataRepository:
    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        copernicus_data_store_api: CopernicusDataStoreAPI,
    ) -> None:
        self.session_maker = session_maker
        self.copernicus_data_store_api = copernicus_data_store_api

    async def download_future_climate_data(self):
        if await self.did_download_future_climate_data():
            logging.info("Already downloaded future climate data")
            return

        def download_func():
            df = self.copernicus_data_store_api.get_future_climate_data()
            return df

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            future_climate_data_df = await loop.run_in_executor(
                executor=pool, func=download_func
            )

        async with self.session_maker() as session:
            stmt = delete(FutureClimateData)
            await session.execute(stmt)
            processed = 0
            STEP = 100
            while processed < len(future_climate_data_df):
                rows = future_climate_data_df[processed : processed + STEP]
                values_dicts: list[dict[str, Any]] = []
                for index, row in rows.iterrows():
                    values_dicts.append(
                        {
                            "id": uuid.uuid4(),
                            "longitude": row["longitude"],
                            "latitude": row["latitude"],
                            "year": cast(pd.MultiIndex, index)[0],
                            "month": cast(pd.MultiIndex, index)[1],
                            "coordinates": coordinates_to_well_known_text(
                                longitude=row["longitude"], latitude=row["latitude"]
                            ),
                            "u_component_of_wind_10m": row["10m_u_component_of_wind"],
                            "v_component_of_wind_10m": row["10m_v_component_of_wind"],
                            "temperature_2m": row["2m_temperature"],
                            "evaporation": row["evaporation"],
                            "total_precipitation": row["total_precipitation"],
                            "surface_pressure": row["surface_pressure"],
                            "surface_solar_radiation_downwards": row[
                                "surface_solar_radiation_downwards"
                            ],
                            "surface_thermal_radiation_downwards": row[
                                "surface_thermal_radiation_downwards"
                            ],
                        }
                    )
                await session.execute(insert(FutureClimateData).values(values_dicts))
                processed += len(rows)
            await session.commit()
        logging.info(f"Saved {processed} future climate data")

    async def did_download_future_climate_data(self) -> bool:
        async with self.session_maker() as session:
            stmt = select(FutureClimateData.year).limit(1)
            result = await session.scalar(stmt)
        return result is not None

    async def get_future_climate_data_for_coordinates(
        self, longitude: float, latitude: float
    ) -> list[FutureClimateDataDTO]:
        point_well_known_text = f"POINT({longitude} {latitude})"
        async with self.session_maker() as session:
            stmt = (
                select(
                    FutureClimateData,
                )
                .order_by(
                    asc(ST_Distance(
                        FutureClimateData.coordinates,
                        sqlalchemy.cast(point_well_known_text, Geography),
                    ))
                )
                .limit(1)
            )
            results = list(await session.scalars(stmt))
        if len(results) is None:
            raise Exception(
                f"Can't find future climate data for {longitude} {latitude}"
            )
        return [self.__future_climate_data_model_to_dto(result) for result in results]

    def __future_climate_data_model_to_dto(
        self, future_climate_data: FutureClimateData
    ) -> FutureClimateDataDTO:
        return FutureClimateDataDTO(
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

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import logging
from uuid import UUID
import uuid
import pandas as pd
from sqlalchemy import asc, delete, desc, insert, select
import sqlalchemy
from tesi.zappai.repositories.dtos import LocationClimateYearsDTO, ClimateDataDTO
from tesi.zappai.models import PastClimateData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Any, cast
from tesi.zappai.repositories.location_repository import LocationRepository
from tesi.zappai.repositories.copernicus_data_store_api import CopernicusDataStoreAPI
from tesi.zappai.utils.common import get_next_n_months


class PastClimateDataRepository:
    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        copernicus_data_store_api: CopernicusDataStoreAPI,
        location_repository: LocationRepository,
    ) -> None:
        self.session_maker = session_maker
        self.copernicus_data_store_api = copernicus_data_store_api
        self.location_repository = location_repository

    async def get_last_past_climate_data(
        self, location_id: UUID
    ) -> ClimateDataDTO | None:
        async with self.session_maker() as session:
            stmt = (
                select(PastClimateData)
                .where(PastClimateData.location_id == location_id)
                .order_by(asc(PastClimateData.year), asc(PastClimateData.month))
                .limit(1)
            )
            result = await session.scalar(stmt)
        if result is None:
            return None
        return self.__past_climate_data_model_to_dto(result)

    async def download_past_climate_data_for_years(
        self, location_id: UUID, years: list[int]
    ):
        location = await self.location_repository.get_location_by_id(location_id)
        if location is None:
            raise ValueError(f"Location {location_id} does not exist in db")

        loop = asyncio.get_running_loop()

        def download_func():
            def on_save_chunk(chunk: pd.DataFrame):
                return asyncio.run_coroutine_threadsafe(
                    coro=self.__save_past_climate_data(
                        location_id=location_id, past_climate_data_df=chunk
                    ),
                    loop=loop,
                ).result()

            self.copernicus_data_store_api.get_past_climate_data_for_years(
                longitude=location.longitude,
                latitude=location.latitude,
                years=years,
                on_save_chunk=on_save_chunk,
            )

        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(executor=pool, func=download_func)

    async def download_new_past_climate_data(self, location_id: UUID):

        year_from = 1940
        month_from = 1

        last_climate_data = await self.get_last_past_climate_data(
            location_id=location_id
        )

        if last_climate_data is not None:
            max_year = last_climate_data.year
            max_month = last_climate_data.month

            year_from, month_from = get_next_n_months(
                n=1, month=max_month, year=max_year
            )

        location = await self.location_repository.get_location_by_id(location_id)

        now = datetime.now(tz=timezone.utc)
        if now.year == year_from and now.month == month_from:
            logging.info(
                f"No new past climate data to download for location_id {location_id}"
            )
        if location is None:
            raise ValueError(f"Location {location_id} does not exist in db")

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:

            def download_func():
                def on_save_chunk(chunk: pd.DataFrame):
                    return asyncio.run_coroutine_threadsafe(
                        coro=self.__save_past_climate_data(
                            location_id=location_id, past_climate_data_df=chunk
                        ),
                        loop=loop,
                    ).result()

                self.copernicus_data_store_api.get_past_climate_data(
                    year_from=year_from,
                    month_from=month_from,
                    longitude=location.longitude,
                    latitude=location.latitude,
                    on_save_chunk=on_save_chunk,
                )

            await loop.run_in_executor(executor=pool, func=download_func)

    async def __save_past_climate_data(
        self, location_id: UUID, past_climate_data_df: pd.DataFrame
    ):
        if len(past_climate_data_df) == 0:
            return
        async with self.session_maker() as session:
            # delete the data of the same period as this dataframe
            years = cast(
                list[int],
                past_climate_data_df.index.get_level_values("year").unique().tolist(),
            )
            stmt = delete(PastClimateData).where(
                (PastClimateData.location_id == location_id)
                & (PastClimateData.year.in_(years))
            )
            await session.execute(stmt)
            values_dicts: list[dict[str, Any]] = []
            for index, row in past_climate_data_df.iterrows():
                index = cast(pd.MultiIndex, index)
                year, month = index
                values_dicts.append(
                    {
                        "id": uuid.uuid4(),
                        "location_id": location_id,
                        "year": year,
                        "month": month,
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
                        "surface_net_solar_radiation": row[
                            "surface_net_solar_radiation"
                        ],
                        "surface_net_thermal_radiation": row[
                            "surface_net_thermal_radiation"
                        ],
                        "snowfall": row["snowfall"],
                        "total_cloud_cover": row["total_cloud_cover"],
                        "dewpoint_temperature_2m": row["2m_dewpoint_temperature"],
                        "soil_temperature_level_3": row["soil_temperature_level_3"],
                        "volumetric_soil_water_layer_3": row[
                            "volumetric_soil_water_layer_3"
                        ],
                    }
                )
            await session.execute(insert(PastClimateData), values_dicts)
            await session.commit()
            logging.info(f"Inserted {len(past_climate_data_df)} past climate data.")

    async def get_all_past_climate_data(
        self,
        location_id: UUID,
    ) -> list[ClimateDataDTO]:
        async with self.session_maker() as session:
            stmt = (
                select(PastClimateData)
                .where(PastClimateData.location_id == location_id)
                .order_by(asc(PastClimateData.year), asc(PastClimateData.month))
            )
            results = list(await session.scalars(stmt))
        if len(results) == 0:
            raise Exception(f"Can't find past climate data for location {location_id}")
        return [self.__past_climate_data_model_to_dto(result) for result in results]

    async def get_past_climate_data(
        self,
        location_id: UUID,
        year_from: int,
        month_from: int,
        year_to: int,
        month_to: int,
    ) -> list[ClimateDataDTO]:
        async with self.session_maker() as session:
            stmt = (
                select(PastClimateData)
                .where(
                    (PastClimateData.location_id == location_id)
                    & (
                        (
                            (PastClimateData.year > year_from)
                            | (
                                (PastClimateData.year == year_from)
                                & (PastClimateData.month >= month_from)
                            )
                        )
                        & (
                            (PastClimateData.year < year_to)
                            | (
                                (PastClimateData.year == year_to)
                                & (PastClimateData.month <= month_to)
                            )
                        )
                    )
                )
                .order_by(asc(PastClimateData.year), asc(PastClimateData.month))
            )
            results = list(await session.scalars(stmt))
        if len(results) == 0:
            raise Exception(
                f"Can't find past climate data for location {location_id}, year_from={year_from}, month_from={month_from}, year_to={year_to}, month_to={month_to}"
            )
        return [self.__past_climate_data_model_to_dto(result) for result in results]

    async def get_past_climate_data_of_previous_n_months(
        self, location_id: UUID, n: int
    ) -> list[ClimateDataDTO]:
        async with self.session_maker() as session:
            stmt = (
                select(
                    PastClimateData,
                )
                .where(PastClimateData.location_id == location_id)
                .order_by(
                    desc(PastClimateData.year),
                    desc(PastClimateData.month),
                )
                .limit(n)
            )
            results = list(await session.scalars(stmt))
        if len(results) is None:
            raise Exception(
                f"Can't find past climate data of previous 12 months for location"
            )
        results.sort(
            key=lambda past_climate_data: (
                past_climate_data.year,
                past_climate_data.month,
            )
        )
        return [self.__past_climate_data_model_to_dto(result) for result in results]

    async def get_unique_location_climate_years(
        self,
    ) -> list[LocationClimateYearsDTO]:
        async with self.session_maker() as session:
            stmt = (
                select(
                    PastClimateData.location_id,
                    PastClimateData.year,
                )
                .order_by(asc(PastClimateData.location_id), asc(PastClimateData.year))
                .distinct()
            )
            results = list(await session.execute(stmt))

        location_id_to_years_dict: dict[uuid.UUID, set[int]] = {}
        for result in results:
            location_id, year = result.tuple()
            if location_id_to_years_dict.get(location_id) is None:
                location_id_to_years_dict.update({location_id: set()})
            location_id_to_years_dict[location_id].add(year)

        return [
            LocationClimateYearsDTO(location_id=location_id, years=years)
            for location_id, years in location_id_to_years_dict.items()
        ]

    def __past_climate_data_model_to_dto(
        self, past_climate_data: PastClimateData
    ) -> ClimateDataDTO:
        return ClimateDataDTO(
            location_id=past_climate_data.location_id,
            year=past_climate_data.year,
            month=past_climate_data.month,
            u_component_of_wind_10m=past_climate_data.u_component_of_wind_10m,
            v_component_of_wind_10m=past_climate_data.v_component_of_wind_10m,
            temperature_2m=past_climate_data.temperature_2m,
            evaporation=past_climate_data.evaporation,
            total_precipitation=past_climate_data.total_precipitation,
            surface_pressure=past_climate_data.surface_pressure,
            surface_solar_radiation_downwards=past_climate_data.surface_solar_radiation_downwards,
            surface_thermal_radiation_downwards=past_climate_data.surface_thermal_radiation_downwards,
            surface_net_solar_radiation=past_climate_data.surface_net_solar_radiation,
            surface_net_thermal_radiation=past_climate_data.surface_net_thermal_radiation,
            snowfall=past_climate_data.snowfall,
            total_cloud_cover=past_climate_data.total_cloud_cover,
            dewpoint_temperature_2m=past_climate_data.dewpoint_temperature_2m,
            soil_temperature_level_3=past_climate_data.soil_temperature_level_3,
            volumetric_soil_water_layer_3=past_climate_data.volumetric_soil_water_layer_3,
        )

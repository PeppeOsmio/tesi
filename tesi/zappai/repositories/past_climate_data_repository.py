import asyncio
from concurrent.futures import ThreadPoolExecutor
from csv import DictWriter
from datetime import datetime, timezone
import logging
import os
from uuid import UUID
import uuid
import pandas as pd
from sqlalchemy import asc, delete, desc, insert, select
import sqlalchemy
from sqlalchemy.exc import IntegrityError
from tesi.zappai.exceptions import LocationNotFoundError, PastClimateDataNotFoundError
from tesi.zappai.dtos import (
    CropYieldDataDTO,
    LocationClimateYearsDTO,
    ClimateDataDTO,
    PastClimateDataDTO,
)
from tesi.zappai.models import PastClimateData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Any, cast
from tesi.zappai.repositories.location_repository import LocationRepository
from tesi.zappai.repositories.copernicus_data_store_api import CopernicusDataStoreAPI
from tesi.zappai.utils.common import get_next_n_months


class PastClimateDataRepository:
    def __init__(
        self,
        copernicus_data_store_api: CopernicusDataStoreAPI,
        location_repository: LocationRepository,
    ) -> None:
        self.copernicus_data_store_api = copernicus_data_store_api
        self.location_repository = location_repository

    async def download_past_climate_data_for_years(
        self, session: AsyncSession, location_id: UUID, years: list[int]
    ):
        location = await self.location_repository.get_location_by_id(
            session=session, location_id=location_id
        )
        if location is None:
            raise ValueError(f"Location {location_id} does not exist in db")

        loop = asyncio.get_running_loop()

        def download_func():
            def on_save_chunk(chunk: pd.DataFrame):
                asyncio.run_coroutine_threadsafe(
                    coro=self.__save_past_climate_data(
                        session=session,
                        location_id=location_id,
                        past_climate_data_df=chunk,
                    ),
                    loop=loop,
                ).result()
                logging.info(f"Saved chunk")

            self.copernicus_data_store_api.get_past_climate_data_for_years(
                longitude=location.longitude,
                latitude=location.latitude,
                years=years,
                on_save_chunk=on_save_chunk,
            )

        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(executor=pool, func=download_func)

    async def download_new_past_climate_data(
        self, session: AsyncSession, location_id: UUID
    ):
        year_from = 1940
        month_from = 1

        last_climate_data: ClimateDataDTO | None = None
        try:
            last_climate_data = (
                await self.get_past_climate_data_of_previous_n_months(
                    session=session, location_id=location_id, n=1
                )
            )[0]
        except PastClimateDataNotFoundError:
            pass

        if last_climate_data is not None:
            max_year = last_climate_data.year
            max_month = last_climate_data.month

            year_from, month_from = get_next_n_months(
                n=1, month=max_month, year=max_year
            )

        location = await self.location_repository.get_location_by_id(
            session=session, location_id=location_id
        )

        now = datetime.now(tz=timezone.utc)
        if now.year == year_from and now.month == month_from:
            logging.info(
                f"No new past climate data to download for location_id {location_id}"
            )
        if location is None:
            raise ValueError(f"Location {location_id} does not exist in db")

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:

            def on_save_chunk(chunk: pd.DataFrame):
                asyncio.run_coroutine_threadsafe(
                    coro=self.__save_past_climate_data(
                        session=session,
                        location_id=location_id,
                        past_climate_data_df=chunk,
                    ),
                    loop=loop,
                ).result()

            await loop.run_in_executor(
                executor=pool,
                func=lambda: self.copernicus_data_store_api.get_past_climate_data(
                    year_from=year_from,
                    month_from=month_from,
                    longitude=location.longitude,
                    latitude=location.latitude,
                    on_save_chunk=on_save_chunk,
                ),
            )

    async def __save_past_climate_data(
        self,
        session: AsyncSession,
        location_id: UUID,
        past_climate_data_df: pd.DataFrame,
    ):
        """This function runs session.commit() at the end to ensure incremental saving

        Args:
            session (AsyncSession): _description_
            location_id (UUID): _description_
            past_climate_data_df (pd.DataFrame): _description_
        """
        if len(past_climate_data_df) == 0:
            logging.info(f"No past climate data, returning")
            return
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
                    "surface_net_solar_radiation": row["surface_net_solar_radiation"],
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
        self, session: AsyncSession, location_id: UUID
    ) -> list[PastClimateDataDTO]:
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
        session: AsyncSession,
        location_id: UUID,
        year_from: int,
        month_from: int,
        year_to: int,
        month_to: int,
    ) -> list[PastClimateDataDTO]:
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
        self, session: AsyncSession, location_id: UUID, n: int | None = None
    ) -> list[PastClimateDataDTO]:
        stmt = (
            select(
                PastClimateData,
            )
            .where(PastClimateData.location_id == location_id)
            .order_by(
                desc(PastClimateData.year),
                desc(PastClimateData.month),
            )
        )
        if n is not None:
            stmt = stmt.limit(n)
        results = list(await session.scalars(stmt))
        if len(results) == 0:
            raise PastClimateDataNotFoundError(
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
        session: AsyncSession,
    ) -> list[LocationClimateYearsDTO]:
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

    async def export_to_csv(
        self,
        session: AsyncSession,
        csv_path: str,
        crop_yield_data: list[CropYieldDataDTO],
    ):

        def open_csv_file():
            return open(csv_path, "w")

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            csv_file = await loop.run_in_executor(executor=pool, func=open_csv_file)
            total_past_climate_data: list[PastClimateDataDTO] = []
            for item in crop_yield_data:
                past_climate_data = await self.get_past_climate_data(
                    session=session,
                    location_id=item.location_id,
                    year_from=item.sowing_year,
                    month_from=item.sowing_month,
                    year_to=item.harvest_year,
                    month_to=item.harvest_month,
                )
                total_past_climate_data.extend(past_climate_data)
            total_past_climate_data_df = PastClimateDataDTO.from_list_to_dataframe(
                total_past_climate_data
            )
            total_past_climate_data_df = total_past_climate_data_df.reset_index()
            dicts = cast(
                list[dict[str, Any]],
                total_past_climate_data_df.to_dict(orient="records"),
            )
            with csv_file:
                csv_writer: DictWriter | None = None
                location_id_to_country_name: dict[UUID, tuple[str, str]] = {}

                for dct in dicts:
                    location_tuple = location_id_to_country_name.get(dct["location_id"])
                    if location_tuple is None:
                        location = await self.location_repository.get_location_by_id(
                            session=session, location_id=dct["location_id"]
                        )
                        if location is None:
                            raise LocationNotFoundError(str(dct["location_id"]))
                        location_tuple = location.country, location.name
                        location_id_to_country_name.update(
                            {dct["location_id"]: location_tuple}
                        )
                    dct.pop("location_id")
                    location_country, location_name = location_tuple
                    dct.update(
                        {
                            "location_country": location_country,
                            "location_name": location_name,
                        }
                    )

                def write_to_csv():
                    nonlocal csv_writer
                    if csv_writer is None:
                        csv_writer = DictWriter(
                            csv_file,
                            fieldnames=dicts[0].keys(),
                        )
                        csv_writer.writeheader()
                    csv_writer.writerows(dicts)

                await loop.run_in_executor(executor=pool, func=write_to_csv)

        logging.info(len(location_id_to_country_name.keys()))
        logging.info(f"TOTAL: {len(total_past_climate_data_df)}")

    async def import_from_csv(self, session: AsyncSession, csv_path: str):
        def read_csv() -> pd.DataFrame:
            return pd.read_csv(csv_path)

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            data = await loop.run_in_executor(executor=pool, func=read_csv)

        dicts = cast(list[dict[str, Any]], data.to_dict(orient="records"))
        for dct in dicts:
            location = await self.location_repository.get_location_by_country_and_name(
                session=session,
                country=dct["location_country"],
                name=dct["location_name"],
            )
            if location is None:
                raise LocationNotFoundError()
            await session.execute(
                delete(PastClimateData).where(
                    (PastClimateData.location_id == location.id)
                    & (PastClimateData.year == dct["year"])
                    & (PastClimateData.month == dct["month"])
                )
            )
            columns_mappings = {
                "10m_u_component_of_wind": "u_component_of_wind_10m",
                "10m_v_component_of_wind": "v_component_of_wind_10m",
                "2m_temperature": "temperature_2m",
                "2m_dewpoint_temperature": "dewpoint_temperature_2m",
            }
            for key, value in columns_mappings.items():
                dct[value] = dct[key]
                dct.pop(key)
            dct["location_id"] = location.id
            dct.pop("location_country")
            dct.pop("location_name")
            dct.update({"id": uuid.uuid4()})
            stmt = insert(PastClimateData).values(**dct)
            await session.execute(stmt)

    def __past_climate_data_model_to_dto(
        self, past_climate_data: PastClimateData
    ) -> PastClimateDataDTO:
        return PastClimateDataDTO(
            location_id=past_climate_data.location_id,
            year=past_climate_data.year,
            month=past_climate_data.month,
            u_component_of_wind_10m=past_climate_data.u_component_of_wind_10m,
            v_component_of_wind_10m=past_climate_data.v_component_of_wind_10m,
            evaporation=past_climate_data.evaporation,
            surface_pressure=past_climate_data.surface_pressure,
            temperature_2m=past_climate_data.temperature_2m,
            total_precipitation=past_climate_data.total_precipitation,
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

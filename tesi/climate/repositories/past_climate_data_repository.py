import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from geoalchemy2 import Geography
import pandas as pd
from sqlalchemy import delete, func, select
import sqlalchemy
from tesi.climate.dtos import PastClimateDataDTO
from tesi.climate.models import FutureClimateData, PastClimateData
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_Distance
from typing import cast
from tesi.climate.utils.common import coordinates_to_well_known_text
from tesi.climate.utils.copernicus_data_store_api import CopernicusDataStoreAPI


class PastClimateDataRepository:
    def __init__(
        self,
        db_session: AsyncSession,
        copernicus_data_store_api: CopernicusDataStoreAPI,
    ) -> None:
        self.db_session = db_session
        self.copernicus_data_store_api = copernicus_data_store_api

    async def download_new_past_climate_data(
        self, longitude: float, latitude: float, cache: bool
    ) -> pd.DataFrame:
        async with self.db_session as session:
            stmt = select(
                func.max(FutureClimateData.year), func.max(FutureClimateData.month)
            )
            result = (await session.execute(stmt)).first()
        # the initial data available from CDS's ERA5 dataset
        max_year: int | None = None
        max_month: int | None = None
        print(f"result: {result}")
        if result is not None and result[0] is not None:
            max_year, max_month = result.tuple()
        year_from = max_year if max_year is not None else 1940
        month_from = (max_month + 1) if max_month is not None else 1
        if max_month == 12:
            year_from += 1
            month_from = 1

        print(f"max_year: {max_year}")
        print(f"max_month: {max_month}")
        print(f"year_from: {year_from}")
        print(f"month_from: {month_from}")

        def download_func():
            csv_path = "training_data/past_climate_data.csv"
            if cache and os.path.exists(csv_path):
                df = pd.read_csv(csv_path, index_col=["year", "month"])
                df = df[
                    (df.index.get_level_values("year") >= year_from)
                    & (df.index.get_level_values("month") >= month_from)
                ]
                return df
            df = self.copernicus_data_store_api.get_past_climate_data(
                longitude=longitude,
                latitude=latitude,
                year_from=year_from,
                month_from=month_from,
            )
            if cache:
                df.to_csv(csv_path)
            return df

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(executor=pool, func=download_func)
        return result

    async def save_past_climate_data(self, past_climate_data_df: pd.DataFrame):
        async with self.db_session as session:
            STEP = 50
            PROCESSED = 0
            while PROCESSED < len(past_climate_data_df):
                row = past_climate_data_df[PROCESSED : PROCESSED + STEP]
                for index, row in past_climate_data_df.iterrows():
                    index = cast(pd.MultiIndex, index)
                    year, month = index
                    coordinates_wkt = coordinates_to_well_known_text(
                        longitude=row["longitude"], latitude=row["latitude"]
                    )
                    past_climate_data = PastClimateData(
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
                        surface_net_solar_radiation=row["surface_net_solar_radiation"],
                        surface_net_thermal_radiation=row["surface_net_thermal_radiation"],
                        precipitation_type=row["precipitation_type"],
                        snowfall=row["snowfall"],
                        total_cloud_cover=row["total_cloud_cover"],
                        dewpoint_temperature_2m=row["2m_dewpoint_temperature"],
                        soil_temperature_level_1=row["soil_temperature_level_1"],
                        volumetric_soil_water_layer_1=row["volumetric_soil_water_layer_1"],
                    )
                session.add(past_climate_data)
                PROCESSED += len(row)
            await session.commit()

    async def get_past_climate_data_for_coordinates(
        self, longitude: float, latitude: float
    ) -> list[PastClimateDataDTO]:
        point_well_known_text = f"POINT({longitude} {latitude})"
        async with self.db_session as session:
            stmt = select(
                PastClimateData,
            ).order_by(
                ST_Distance(
                    PastClimateData.coordinates,
                    sqlalchemy.cast(point_well_known_text, Geography),
                )
            )
            results = list(await session.scalars(stmt))
        if len(results) == 0:
            raise Exception(f"Can't find past climate data for {longitude} {latitude}")
        return self.__past_climate_data_models_to_dtos(results)

    async def get_past_climate_data_of_previous_12_months(
        self, longitude: float, latitude: float
    ) -> list[PastClimateDataDTO]:
        point_well_known_text = f"POINT({longitude} {latitude})"
        async with self.db_session as session:
            stmt = (
                select(
                    PastClimateData,
                )
                .order_by(
                    ST_Distance(
                        PastClimateData.coordinates,
                        sqlalchemy.cast(point_well_known_text, Geography),
                    ),
                    PastClimateData.year,
                    PastClimateData.month,
                )
                .limit(12)
            )
            results = list(await session.scalars(stmt))
        if len(results) is None:
            raise Exception(
                f"Can't find past climate data of previous 12 months for {longitude} {latitude}"
            )
        return self.__past_climate_data_models_to_dtos(results)

    def __past_climate_data_models_to_dtos(
        self, lst: list[PastClimateData]
    ) -> list[PastClimateDataDTO]:
        past_climate_data_list: list[PastClimateDataDTO] = []
        for past_climate_data in lst:
            past_climate_data_list.append(
                PastClimateDataDTO(
                    year=past_climate_data.year,
                    month=past_climate_data.month,
                    longitude=past_climate_data.longitude,
                    latitude=past_climate_data.latitude,
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
                    precipitation_type=past_climate_data.precipitation_type,
                    snowfall=past_climate_data.snowfall,
                    total_cloud_cover=past_climate_data.total_cloud_cover,
                    dewpoint_temperature_2m=past_climate_data.dewpoint_temperature_2m,
                    soil_temperature_level_1=past_climate_data.soil_temperature_level_1,
                    volumetric_soil_water_layer_1=past_climate_data.volumetric_soil_water_layer_1,
                )
            )
        return past_climate_data_list

from __future__ import annotations
from dataclasses import dataclass

import pandas as pd

from typing import cast


@dataclass
class FutureClimateDataDTO:
    year: int
    month: int
    longitude: float
    latitude: float

    u_component_of_wind_10m: float
    v_component_of_wind_10m: float
    temperature_2m: float
    evaporation: float
    total_precipitation: float
    surface_pressure: float
    surface_solar_radiation_downwards: float
    surface_thermal_radiation_downwards: float

    @staticmethod
    def from_list_to_dataframe(list: list[FutureClimateDataDTO]) -> pd.DataFrame:
        df = pd.DataFrame([obj.__dict__ for obj in list])
        df.rename(
            columns={
                "u_component_of_wind_10m": "10m_u_component_of_wind",
                "v_component_of_wind_10m": "10m_v_component_of_wind",
                "temperature_2m": "2m_temperature",
            },
            inplace=True,
        )
        return df

    @staticmethod
    def from_dataframe_to_list(df: pd.DataFrame) -> list[FutureClimateDataDTO]:
        tmp_df = df.rename(
            columns={
                "10m_u_component_of_wind": "u_component_of_wind_10m",
                "10m_v_component_of_wind": "v_component_of_wind_10m",
                "2m_temperature": "temperature_2m",
            },
        )
        result: list[FutureClimateDataDTO] = []
        for index, row in tmp_df.iterrows():
            year, month = cast(pd.MultiIndex, index)
            result.append(FutureClimateDataDTO(year=year, month=month, **row.to_dict()))
        return result


@dataclass
class PastClimateDataDTO:
    year: int
    month: int
    longitude: float
    latitude: float

    u_component_of_wind_10m: float
    v_component_of_wind_10m: float
    temperature_2m: float
    evaporation: float
    total_precipitation: float
    surface_pressure: float
    surface_solar_radiation_downwards: float
    surface_thermal_radiation_downwards: float

    surface_net_solar_radiation: float
    surface_net_thermal_radiation: float
    precipitation_type: float
    snowfall: float
    total_cloud_cover: float
    dewpoint_temperature_2m: float
    soil_temperature_level_1: float
    volumetric_soil_water_layer_1: float

    @staticmethod
    def from_list_to_dataframe(lst: list[PastClimateDataDTO]) -> pd.DataFrame:
        df = pd.DataFrame([item.__dict__ for item in lst])
        df.rename(
            columns={
                "u_component_of_wind_10m": "10m_u_component_of_wind",
                "v_component_of_wind_10m": "10m_v_component_of_wind",
                "temperature_2m": "2m_temperature",
                "dewpoint_temperature_2m": "2m_dewpoint_temperature",
            },
            inplace=True,
        )
        return df

    @staticmethod
    def from_dataframe_to_list(df: pd.DataFrame) -> list[PastClimateDataDTO]:
        tmp_df = df.rename(
            columns={
                "10m_u_component_of_wind": "u_component_of_wind_10m",
                "10m_v_component_of_wind": "v_component_of_wind_10m",
                "2m_temperature": "temperature_2m",
                "2m_dewpoint_temperature": "dewpoint_temperature_2m",
            },
        )
        result: list[PastClimateDataDTO] = []
        for index, row in tmp_df.iterrows():
            year, month = cast(pd.MultiIndex, index)
            result.append(PastClimateDataDTO(year=year, month=month, **row.to_dict()))
        return result

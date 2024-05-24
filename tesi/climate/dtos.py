from __future__ import annotations
from dataclasses import dataclass

import pandas as pd

from tesi.climate.models import Month


@dataclass
class FutureClimateDataDTO:
    year: int
    month: Month
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
    def from_list_to_dataframe(lst: list[FutureClimateDataDTO]) -> pd.DataFrame:
        df = pd.DataFrame([item.__dict__ for item in lst])
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
        tmp_df = df.copy()
        tmp_df.rename(
            columns={
                "10m_u_component_of_wind": "u_component_of_wind_10m",
                "10m_v_component_of_wind": "v_component_of_wind_10m",
                "2m_temperature": "temperature_2m",
            },
            inplace=True,
        )
        return [FutureClimateDataDTO(**row.to_dict()) for i, row in df.iterrows()]


@dataclass
class PastClimateDataDTO:
    year: int
    month: Month
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
        tmp_df = df.copy()
        tmp_df.rename(
            columns={
                "10m_u_component_of_wind": "u_component_of_wind_10m",
                "10m_v_component_of_wind": "v_component_of_wind_10m",
                "2m_temperature": "temperature_2m",
                "2m_dewpoint_temperature": "dewpoint_temperature_2m",
            },
            inplace=True,
        )
        return [PastClimateDataDTO(**row.to_dict()) for i, row in df.iterrows()]

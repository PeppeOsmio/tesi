from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from keras.src.models import Sequential
import pandas as pd

from typing import cast

from sklearn.preprocessing import MinMaxScaler


@dataclass
class LocationClimateYearsDTO:
    location_id: UUID
    years: set[int]


@dataclass
class CropDTO:
    id: UUID
    name: str
    created_at: datetime


@dataclass
class LocationDTO:
    id: UUID
    country: str
    name: str
    longitude: float
    latitude: float
    created_at: datetime


@dataclass
class ClimateGenerativeModelDTO:
    id: UUID
    location_id: UUID
    model: Sequential
    x_scaler: MinMaxScaler
    y_scaler: MinMaxScaler


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
        df = df.rename(
            columns={
                "u_component_of_wind_10m": "10m_u_component_of_wind",
                "v_component_of_wind_10m": "10m_v_component_of_wind",
                "temperature_2m": "2m_temperature",
            },
        )
        df = df.set_index(keys=["year", "month"], drop=True)
        df = df.sort_index(ascending=[True, True])
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
class ClimateDataDTO:
    location_id: UUID
    year: int
    month: int

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
    snowfall: float
    total_cloud_cover: float
    dewpoint_temperature_2m: float
    soil_temperature_level_1: float
    volumetric_soil_water_layer_1: float

    @staticmethod
    def from_list_to_dataframe(lst: list[ClimateDataDTO]) -> pd.DataFrame:
        df = pd.DataFrame([item.__dict__ for item in lst])
        df = df.rename(
            columns={
                "u_component_of_wind_10m": "10m_u_component_of_wind",
                "v_component_of_wind_10m": "10m_v_component_of_wind",
                "temperature_2m": "2m_temperature",
                "dewpoint_temperature_2m": "2m_dewpoint_temperature",
            },
        )
        df = df.drop(columns=["location_id"])
        df = df.set_index(keys=["year", "month"], drop=True)
        df = df.sort_index(ascending=[True, True])
        return df

    @staticmethod
    def from_dataframe_to_list(df: pd.DataFrame) -> list[ClimateDataDTO]:
        tmp_df = df.rename(
            columns={
                "10m_u_component_of_wind": "u_component_of_wind_10m",
                "10m_v_component_of_wind": "v_component_of_wind_10m",
                "2m_temperature": "temperature_2m",
                "2m_dewpoint_temperature": "dewpoint_temperature_2m",
            },
        )
        result: list[ClimateDataDTO] = []
        for index, row in tmp_df.iterrows():
            year, month = cast(pd.MultiIndex, index)
            result.append(ClimateDataDTO(year=year, month=month, **row.to_dict()))
        return result

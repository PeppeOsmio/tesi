from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from keras.src.models import Sequential
import pandas as pd

from typing import Any, cast

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

@dataclass
class SoilTypeDTO:
    id: UUID
    name: str

@dataclass
class LocationClimateYearsDTO:
    location_id: UUID
    years: set[int]


@dataclass
class CropDTO:
    id: UUID
    name: str
    created_at: datetime
    min_farming_months: int
    max_farming_months: int
    crop_yield_model: RandomForestRegressor | None
    mse: float | None
    r2: float | None


@dataclass
class CropYieldDataDTO:
    id: UUID
    location_id: UUID
    crop_id: UUID
    sowing_year: int
    sowing_month: int
    harvest_year: int
    harvest_month: int
    duration_months: int
    yield_per_hectar: float

    @staticmethod
    def from_list_to_dataframe(lst: list[CropYieldDataDTO]) -> pd.DataFrame:
        df = pd.DataFrame([obj.__dict__ for obj in lst])
        df = df.sort_values(by=["sowing_year", "sowing_month"])
        df = df.reset_index()
        return df


@dataclass
class LocationDTO:
    id: UUID
    country: str
    name: str
    longitude: float
    latitude: float
    created_at: datetime
    soil_type_id: UUID

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "country": self.country,
            "name": self.name,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "created_at": self.created_at.isoformat(),
            "soil_type_id": str(self.soil_type_id)
        }


@dataclass
class ClimateGenerativeModelDTO:
    id: UUID
    location_id: UUID
    model: Sequential
    x_scaler: StandardScaler
    y_scaler: StandardScaler
    rmse: float

    train_start_year: int
    train_start_month: int
    train_end_year: int
    train_end_month: int

    validation_start_year: int
    validation_start_month: int
    validation_end_year: int
    validation_end_month: int

    test_start_year: int
    test_start_month: int
    test_end_year: int
    test_end_month: int


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
    def from_list_to_dataframe(lst: list[FutureClimateDataDTO]) -> pd.DataFrame:
        df = pd.DataFrame([obj.__dict__ for obj in lst])
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

    # u_component_of_wind_10m: float
    # v_component_of_wind_10m: float
    # evaporation: float
    # surface_pressure: floats
    temperature_2m: float
    total_precipitation: float
    surface_solar_radiation_downwards: float
    surface_thermal_radiation_downwards: float

    surface_net_solar_radiation: float
    surface_net_thermal_radiation: float
    # snowfall: float
    total_cloud_cover: float
    dewpoint_temperature_2m: float
    soil_temperature_level_3: float
    volumetric_soil_water_layer_3: float

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
from enum import IntEnum
from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column
from tesi.database.base import Base
from geoalchemy2 import Geography


class PastClimateData(Base):
    __tablename__ = "past_climate_data"

    longitude: Mapped[float] = mapped_column(primary_key=True)
    latitude: Mapped[float] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    month: Mapped[int] = mapped_column(primary_key=True)

    coordinates: Mapped[Geography] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
    )

    u_component_of_wind_10m: Mapped[float]
    v_component_of_wind_10m: Mapped[float]
    temperature_2m: Mapped[float]
    evaporation: Mapped[float]
    total_precipitation: Mapped[float]
    surface_pressure: Mapped[float]
    surface_solar_radiation_downwards: Mapped[float]
    surface_thermal_radiation_downwards: Mapped[float]

    surface_net_solar_radiation: Mapped[float]
    surface_net_thermal_radiation: Mapped[float]
    precipitation_type: Mapped[float]
    snowfall: Mapped[float]
    total_cloud_cover: Mapped[float]
    dewpoint_temperature_2m: Mapped[float]
    soil_temperature_level_1: Mapped[float]
    volumetric_soil_water_layer_1: Mapped[float]


class FutureClimateData(Base):
    __tablename__ = "future_climate_data"

    longitude: Mapped[int] = mapped_column(primary_key=True)
    latitude: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    month: Mapped[int] = mapped_column(primary_key=True)

    coordinates: Mapped[Geography] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
    )

    u_component_of_wind_10m: Mapped[float]
    v_component_of_wind_10m: Mapped[float]
    temperature_2m: Mapped[float]
    evaporation: Mapped[float]
    total_precipitation: Mapped[float]
    surface_pressure: Mapped[float]
    surface_solar_radiation_downwards: Mapped[float]
    surface_thermal_radiation_downwards: Mapped[float]

from enum import IntEnum
from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column
from tesi.database.base import Base
from geoalchemy2 import Geography


class Month(IntEnum):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12


class FutureClimateData(Base):
    __tablename__ = "future_climate_data"
    coordinates_str: Mapped[str] = mapped_column(primary_key=True)
    coordinates: Mapped[Geography] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
    )
    year: Mapped[int] = mapped_column(primary_key=True)
    month: Mapped[Month] = mapped_column(primary_key=True)
    
    u_component_of_wind_10m: Mapped[float]
    v_component_of_wind_10m: Mapped[float]
    temperature_2m: Mapped[float]
    evaporation: Mapped[float]
    total_precipitation: Mapped[float]
    surface_pressure: Mapped[float]
    surface_solar_radiation_downwards: Mapped[float]
    surface_thermal_radiation_downwards: Mapped[float]

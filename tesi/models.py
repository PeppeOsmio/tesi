from enum import IntEnum
from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column
from tesi.database.base import Base
from geoalchemy2 import Geography


class Months(IntEnum):
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
    coordinates: Mapped[Geography] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), primary_key=True
    )
    year: Mapped[int]
    month: Mapped[Months] = mapped_column(primary_key=True)
    precipitations: Mapped[float]
    surface_temperature: Mapped[float]

class CropData(Base):
    ...
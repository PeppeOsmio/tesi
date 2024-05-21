from dataclasses import dataclass

from tesi.climate.models import Month



@dataclass
class FutureClimateDataDTO:
    year: int
    month: Month
    latitude: float
    longitude: float
    precipitations: float
    surface_temperature: float

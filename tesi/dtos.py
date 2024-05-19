from dataclasses import dataclass


@dataclass
class ClimateDataDTO:
    latitude: float
    longitude: float
    precipitations: float
    temperature_at_surface: float

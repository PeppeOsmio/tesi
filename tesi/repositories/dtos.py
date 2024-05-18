from dataclasses import dataclass


@dataclass
class PredictionDTO:
    year: int
    month: int
    lon: float
    lat: float
    precipitations: float
    temperature_at_surface: float
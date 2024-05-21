from dataclasses import dataclass


@dataclass
class FutureClimateDataDTO:
    year: int
    month: int
    longitude: float
    latitude: float
    total_precipitations: float
    surface_temperature: float


@dataclass
class PastClimateDataDTO:
    year: int
    month: int
    longitude: float
    latitude: float
    total_precipitations: float
    surface_temperature: float
    surface_net_solar_radiation: float
    surface_pressure: float
    volumetric_soil_water_layer_1: float
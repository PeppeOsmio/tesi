from dataclasses import dataclass


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
    precipitation_type: int
    mean_precipitation_flux: float
    surface_pressure: float
    surface_solar_radiation_downwards: float
    surface_thermal_radiation_downwards: float
    surface_net_solar_radiation: float
    surface_net_thermal_radiation: float


@dataclass
class PastClimateDataDTO:
    year: int
    month: int
    longitude: float
    latitude: float
    # common to Future and Past
    u_component_of_wind_10m: float
    v_component_of_wind_10m: float
    temperature_2m: float
    evaporation: float
    precipitation_type: int
    total_precipitation: float
    surface_pressure: float
    surface_solar_radiation_downwards: float
    surface_thermal_radiation_downwards: float
    surface_net_solar_radiation: float
    surface_net_thermal_radiation: float
    # exclusive to Past 
    snowfall: float
    total_cloud_cover: float
    dewpoint_temperature_2m: float
    soil_temperature_level_1: float
    volumetric_soil_water_layer_1: float
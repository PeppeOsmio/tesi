from tesi.schemas import CustomBaseModel

class GetPastClimateDataOfLocationResponse(CustomBaseModel):
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
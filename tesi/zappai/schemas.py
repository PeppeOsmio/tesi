from datetime import datetime
from uuid import UUID
from tesi.schemas import CustomBaseModel
from tesi.zappai.dtos import CropDTO
from tesi.zappai.services.crop_optimizer_service import CropOptimizerResultDTO


class GetPastClimateDataOfLocationResponse(CustomBaseModel):
    year: int
    month: int

    temperature_2m: float
    total_precipitation: float
    surface_solar_radiation_downwards: float
    surface_thermal_radiation_downwards: float

    surface_net_solar_radiation: float
    surface_net_thermal_radiation: float
    total_cloud_cover: float
    dewpoint_temperature_2m: float
    soil_temperature_level_1: float
    volumetric_soil_water_layer_1: float


class CreateLocationBody(CustomBaseModel):
    country: str
    name: str
    longitude: float
    latitude: float


class LocationDetailsResponse(CustomBaseModel):
    id: UUID
    country: str
    name: str
    longitude: float
    latitude: float
    last_past_climate_data_year: int | None
    last_past_climate_data_month: int | None

class PredictionsResponse(CustomBaseModel, CropOptimizerResultDTO):
    pass

class CropDetailsResponse(CustomBaseModel):
    id: UUID
    name: str
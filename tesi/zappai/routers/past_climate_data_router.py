from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends

from tesi.zappai.di import get_past_climate_data_repository
from tesi.zappai.repositories.past_climate_data_repository import PastClimateDataRepository
from tesi.zappai.schemas import GetPastClimateDataOfLocationResponse


past_climate_data_router = APIRouter(prefix="/past_climate_data")

@past_climate_data_router.get("/{location_id}", response_model=list[GetPastClimateDataOfLocationResponse])
async def get_past_climate_data_of_location(
    location_id: UUID,
    past_climate_data_repository: Annotated[PastClimateDataRepository, Depends(get_past_climate_data_repository)]
):
    data = await past_climate_data_repository.get_past_climate_data(location_id)
    return [GetPastClimateDataOfLocationResponse(
        year=item.year,
        month=item.month,
        u_component_of_wind_10m=item.u_component_of_wind_10m,
        v_component_of_wind_10m=item.v_component_of_wind_10m,
        temperature_2m=item.temperature_2m,
        evaporation=item.evaporation,
        total_precipitation=item.total_precipitation,
        surface_pressure=item.surface_pressure,
        surface_solar_radiation_downwards=item.surface_solar_radiation_downwards,
        
    ) for item in data]
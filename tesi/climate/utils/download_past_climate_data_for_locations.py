import asyncio
import logging
import os
from typing import cast
import pandas as pd

from tesi.climate.di import (
    get_cds_api,
    get_crop_repository,
    get_crop_yield_data_repository,
    get_location_repository,
    get_past_climate_data_repository,
)
from tesi.climate.dtos import PastClimateDataDTO
from tesi.database.di import get_db_session
from tesi.climate.utils import common


async def main():
    logging.basicConfig(level=logging.INFO)

    db_session = await get_db_session()
    location_repository = get_location_repository(db_session=db_session)
    cds_api = get_cds_api()
    past_climate_data_repository = get_past_climate_data_repository(
        db_session=db_session, cds_api=cds_api, location_repository=location_repository
    )
    crop_repository = get_crop_repository(db_session=db_session)

    crop_yield_data_repository = get_crop_yield_data_repository(
        db_session=db_session,
        crop_repository=crop_repository,
        location_repository=location_repository,
    )

    location_climate_years_from_crop_yield_data = (
        await crop_yield_data_repository.get_unique_location_climate_years()
    )
    location_climate_years_from_past_climate_data = (
        await past_climate_data_repository.get_unique_location_climate_years()
    )

    for location_climate_years in location_climate_years_from_crop_yield_data:
        for tmp in location_climate_years_from_past_climate_data:
            if location_climate_years.location_id == tmp:
                location_climate_years.years = location_climate_years.years - tmp.years
                break

    STEP = 5
    processed = 0
    while processed < len(location_climate_years_from_crop_yield_data):
        items = location_climate_years_from_crop_yield_data[
            processed : processed + STEP
        ]
        await asyncio.gather(
            past_climate_data_repository.download_past_climate_data_for_years(
                location_id=location_climate_years.location_id,
                years=list(location_climate_years.years),
            )
            for location_climate_years in items
        )


if __name__ == "__main__":
    asyncio.run(main())

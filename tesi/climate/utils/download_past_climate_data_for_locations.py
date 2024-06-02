import asyncio
import logging
from typing import Iterable
from uuid import UUID

from tesi.climate.di import (
    get_cds_api,
    get_crop_repository,
    get_crop_yield_data_repository,
    get_location_repository,
    get_past_climate_data_repository,
)
from tesi.database.di import get_session_maker


async def main():
    logging.basicConfig(level=logging.INFO)

    session_maker = get_session_maker()
    location_repository = get_location_repository(session_maker=session_maker)
    cds_api = get_cds_api()
    past_climate_data_repository = get_past_climate_data_repository(
        session_maker=session_maker, cds_api=cds_api, location_repository=location_repository
    )
    crop_repository = get_crop_repository(session_maker=session_maker)

    crop_yield_data_repository = get_crop_yield_data_repository(
        session_maker=session_maker,
        crop_repository=crop_repository,
        location_repository=location_repository,
    )

    logging.info("Getting location and climate data from Crop Yields table")
    location_climate_years_from_crop_yield_data = (
        await crop_yield_data_repository.get_unique_location_climate_years()
    )

    logging.info("Getting location and climate data from Past Climate Data table")
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

        async def coro(id: int, location_id: UUID, years: list[int]):
            logging.info(f"Running coro {id}")
            await past_climate_data_repository.download_past_climate_data_for_years(
                location_id=location_id,
                years=years,
            )

        coroutines = [
            coro(
                id=i,
                location_id=location_climate_years.location_id,
                years=list(location_climate_years.years),
            )
            for i, location_climate_years in enumerate(items)
        ]
        await asyncio.gather(*coroutines)


if __name__ == "__main__":
    asyncio.run(main())

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
from tesi.climate.dtos import LocationClimateYearsDTO
from tesi.database.di import get_session_maker


async def main():
    CONCURRENT_REQUESTS = 5

    session_maker = get_session_maker()
    location_repository = get_location_repository(session_maker=session_maker)
    cds_api = get_cds_api()
    past_climate_data_repository = get_past_climate_data_repository(
        session_maker=session_maker,
        cds_api=cds_api,
        location_repository=location_repository,
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
            if location_climate_years.location_id == tmp.location_id:
                location_climate_years.years = location_climate_years.years - tmp.years
                logging.info(
                    f"{location_climate_years.location_id} {location_climate_years.years}"
                )
                break

    location_climate_years_to_fetch: list[LocationClimateYearsDTO] = [item for item in location_climate_years_from_crop_yield_data if len(item.years) > 0 ]

    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    processed = 0
    logging.info(f"COMPLETED: {processed}/{len(location_climate_years_to_fetch)}")

    async def worker(
        semaphore: asyncio.Semaphore, location_climate_years: LocationClimateYearsDTO
    ):
        async with semaphore:
            await past_climate_data_repository.download_past_climate_data_for_years(
                location_id=location_climate_years.location_id,
                years=list(location_climate_years.years),
            )

    for task in asyncio.as_completed(
        [
            worker(semaphore=semaphore, location_climate_years=location_climate_years)
            for location_climate_years in location_climate_years_to_fetch
        ]
    ):
        await task
        processed += 1
        logging.info(f"COMPLETED: {processed}/{len(location_climate_years_to_fetch)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

import asyncio
import logging

from tesi.climate.di import (
    get_cds_api,
    get_crop_repository,
    get_crop_yield_data_repository,
    get_location_repository,
)
from tesi.database.di import get_session_maker


async def main():

    logging.basicConfig(level=logging.INFO)

    session_maker = get_session_maker()

    cds_api = get_cds_api()

    location_repository = get_location_repository(session_maker=session_maker)

    crop_repository = get_crop_repository(session_maker=session_maker)

    crop_yield_data_repository = get_crop_yield_data_repository(
        session_maker=session_maker,
        crop_repository=crop_repository,
        location_repository=location_repository,
    )

    await crop_yield_data_repository.download_crop_yield_data()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

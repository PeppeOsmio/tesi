import asyncio
import logging

from tesi.climate.di import (
    get_cds_api,
    get_crop_repository,
    get_crop_yield_data_repository,
    get_future_climate_data_repository,
    get_location_repository,
)
from tesi.database.di import get_db_session


async def main():

    logging.basicConfig(level=logging.INFO)

    db_session = await get_db_session()

    cds_api = get_cds_api()

    location_repository = get_location_repository(db_session=db_session)

    crop_repository = get_crop_repository(db_session=db_session)

    crop_yield_data_repository = get_crop_yield_data_repository(
        db_session=db_session,
        crop_repository=crop_repository,
        location_repository=location_repository,
    )

    await crop_yield_data_repository.download_crop_yield_data()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

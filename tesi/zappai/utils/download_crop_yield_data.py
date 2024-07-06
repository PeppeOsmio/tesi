import asyncio
import logging
import traceback

from tesi import logging_conf
from tesi.zappai.di import (
    get_cds_api,
    get_crop_repository,
    get_crop_yield_data_repository,
    get_location_repository,
)
from tesi.database.di import get_session_maker


async def main():

    logging.basicConfig(level=logging.INFO)

    session_maker = get_session_maker()
    location_repository = get_location_repository(session_maker=session_maker)
    crop_repository = get_crop_repository(session_maker=session_maker)
    crop_yield_data_repository = get_crop_yield_data_repository(
        session_maker=session_maker,
        crop_repository=crop_repository,
        location_repository=location_repository,
    )
    retries = 0
    while retries < 1:
        try:
            await crop_yield_data_repository.download_crop_yield_data()
            break
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.info("Failed to fetch past climate data, retrying...")
            retries += 1


if __name__ == "__main__":
    logging_conf.create_logger(config=logging_conf.get_default_conf())
    asyncio.run(main())

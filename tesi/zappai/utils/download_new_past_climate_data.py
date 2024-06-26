import asyncio
import logging
import os
from typing import cast
from uuid import UUID
import pandas as pd

from tesi import logging_conf
from tesi.zappai.di import (
    get_cds_api,
    get_location_repository,
    get_past_climate_data_repository,
)
from tesi.zappai.repositories.dtos import ClimateDataDTO
from tesi.database.di import get_session_maker
from tesi.zappai.utils import common

import traceback


async def main():
    logging.basicConfig(level=logging.INFO)

    session_maker = get_session_maker()
    location_repository = get_location_repository(session_maker=session_maker)
    cds_api = get_cds_api()
    past_climate_data_repository = get_past_climate_data_repository(
        session_maker=session_maker,
        cds_api=cds_api,
        location_repository=location_repository,
    )

    location = await location_repository.get_location_by_country_and_name(
        country=common.EXAMPLE_LOCATION_COUNTRY, name=common.EXAMPLE_LOCATION_NAME
    )
    if location is None:
        location = await location_repository.create_location(
            country=common.EXAMPLE_LOCATION_COUNTRY,
            name=common.EXAMPLE_LOCATION_NAME,
            longitude=common.EXAMPLE_LONGITUDE,
            latitude=common.EXAMPLE_LATITUDE,
        )

    location = await location_repository.get_location_by_id(location_id=UUID(hex="3d3b83c1-9dd2-4b5b-a06e-bd1f83a8188c"))
    if location is None:
        raise Exception()

    retries = 0
    while retries < 10:
        try:
            await past_climate_data_repository.download_new_past_climate_data(
                location_id=location.id
            )
            break
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.info("Failed to fetch past climate data, retrying...")
            retries += 1


if __name__ == "__main__":
    logging_conf.create_logger(config=logging_conf.get_default_conf())
    asyncio.run(main())

import asyncio
import logging
import os
from typing import cast
import pandas as pd

from tesi import logging_conf
from tesi.climate.di import (
    get_cds_api,
    get_location_repository,
    get_past_climate_data_repository,
)
from tesi.climate.dtos import PastClimateDataDTO
from tesi.database.di import get_session_maker
from tesi.climate.utils import common


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

    await past_climate_data_repository.download_new_past_climate_data(
        location_id=location.id
    )


if __name__ == "__main__":
    logging_conf.create_logger(config=logging_conf.get_default_conf())
    asyncio.run(main())

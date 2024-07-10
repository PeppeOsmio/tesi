import asyncio
import logging
import pandas as pd
from tesi.zappai.repositories.dtos import FutureClimateDataDTO, ClimateDataDTO
from tesi.zappai.di import (
    get_location_repository,
    get_session_maker,
    get_cds_api,
    get_past_climate_data_repository,
    get_future_climate_data_repository,
)
from tesi.zappai import common
import matplotlib.pyplot as plt


async def main():
    session_maker = get_session_maker()
    cds_api = get_cds_api()
    location_repository = get_location_repository(session_maker=session_maker)
    past_climate_data_repository = get_past_climate_data_repository(
        session_maker=session_maker,
        cds_api=cds_api,
        location_repository=location_repository,
    )
    future_climate_data_repository = get_future_climate_data_repository(
        session_maker=session_maker, cds_api=cds_api
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

    past_climate_data_df = ClimateDataDTO.from_list_to_dataframe(
        await past_climate_data_repository.get_all_past_climate_data(location.id)
    )

    past_climate_data_df.to_csv("past_climate_data.csv")

    future_climate_data_df = FutureClimateDataDTO.from_list_to_dataframe(
        await future_climate_data_repository.get_future_climate_data_for_nearest_coordinates(
            longitude=location.longitude,
            latitude=location.latitude,
            year_from=1970,
            month_from=1,
            year_to=9999,
            month_to=12,
        )
    )

    future_climate_data_df.to_csv("future_climate_data.csv")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

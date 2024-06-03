import asyncio
import logging

from tesi import logging_conf
from tesi.climate.di import get_cds_api, get_future_climate_data_repository
from tesi.database.di import get_session_maker


async def main():

    logging.basicConfig(level=logging.INFO)

    session_maker = get_session_maker()

    cds_api = get_cds_api()

    future_climate_data_repository = get_future_climate_data_repository(
        session_maker=session_maker, cds_api=cds_api
    )

    await future_climate_data_repository.download_future_climate_data()


if __name__ == "__main__":
    logging_conf.create_logger(config=logging_conf.get_default_conf())
    asyncio.run(main())

import asyncio
import os
from tesi import logging_conf
from tesi.database.di import get_session_maker
from tesi.zappai.di import (
    get_cds_api,
    get_crop_repository,
    get_crop_yield_data_repository,
    get_future_climate_data_repository,
    get_location_repository,
    get_past_climate_data_repository,
)
import logging


async def main():
    session_maker = get_session_maker()
    location_repository = get_location_repository()
    async with session_maker() as session:

        os.makedirs("training_data", exist_ok=True)

        logging.info("Exporting locations")
        await location_repository.export_to_csv(session=session, csv_path="training_data/locations.csv")


if __name__ == "__main__":
    logging_conf.create_logger(config=logging_conf.get_default_conf())
    asyncio.run(main())

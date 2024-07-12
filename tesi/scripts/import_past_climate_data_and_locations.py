import asyncio
import logging

from tesi import logging_conf
from tesi.database.di import get_session_maker
from tesi.zappai.di import (
    get_cds_api,
    get_crop_repository,
    get_crop_yield_data_repository,
    get_location_repository,
    get_past_climate_data_repository,
)


async def main():
    session_maker = get_session_maker()
    location_repository = get_location_repository(session_maker=session_maker)
    cds_api = get_cds_api()
    past_climate_data_repository = get_past_climate_data_repository(
        session_maker=session_maker,
        cds_api=cds_api,
        location_repository=location_repository,
    )

    logging.info("Import locations")
    await location_repository.import_from_csv(csv_path="training_data/locations.csv")

    logging.info("Importing past climate data")
    await past_climate_data_repository.import_from_csv(csv_path="training_data/past_climate_data.csv")


if __name__ == "__main__":
    logging_conf.create_logger(config=logging_conf.get_default_conf())
    asyncio.run(main())

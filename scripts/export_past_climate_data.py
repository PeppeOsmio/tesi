import asyncio
import os
from tesi import logging_conf
from tesi.database.di import get_session_maker
from tesi.zappai.di import (
    get_cds_api,
    get_crop_repository,
    get_crop_yield_data_repository,
    get_location_repository,
    get_past_climate_data_repository,
)
import logging


async def main():
    session_maker = get_session_maker()
    location_repository = get_location_repository()
    crop_repository = get_crop_repository()
    cds_api = get_cds_api()
    past_climate_data_repository = get_past_climate_data_repository(
        cds_api=cds_api,
        location_repository=location_repository,
    )
    crop_yield_data_repository = get_crop_yield_data_repository(
        crop_repository=crop_repository,
        location_repository=location_repository,
        past_climate_data_repository=past_climate_data_repository,
    )
    async with session_maker() as session:
        os.makedirs("training_data", exist_ok=True)

        logging.info("Exporting past climate data")
        locations = await location_repository.get_locations(session=session, is_visible=False)
        crop_yield_data = await crop_yield_data_repository.get_crop_yield_data_for_locations(session=session, location_ids=[location.id for location in locations])
        await past_climate_data_repository.export_to_csv(
            session=session,
            csv_path="training_data/past_climate_data.csv",
            crop_yield_data=crop_yield_data,
        )

if __name__ == "__main__":
    logging_conf.create_logger(config=logging_conf.get_default_conf())
    asyncio.run(main())

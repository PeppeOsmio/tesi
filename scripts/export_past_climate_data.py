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
        location_ids_and_periods = (
            await crop_yield_data_repository.get_unique_location_and_period_tuples(
                session=session
            )
        )

        os.makedirs("training_data", exist_ok=True)

        logging.info("Exporting past climate data")
        await past_climate_data_repository.export_to_csv(
            session=session,
            csv_path="training_data/past_climate_data.csv",
            location_id_and_periods=location_ids_and_periods,
        )

if __name__ == "__main__":
    logging_conf.create_logger(config=logging_conf.get_default_conf())
    asyncio.run(main())

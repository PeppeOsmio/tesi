import asyncio
import logging
import traceback

from tesi import logging_conf
from tesi.zappai.di import (
    get_cds_api,
    get_crop_repository,
    get_crop_yield_data_repository,
    get_crop_yield_model_service,
    get_location_repository,
    get_past_climate_data_repository,
)
from tesi.database.di import get_session_maker


async def main():

    logging.basicConfig(level=logging.INFO)

    session_maker = get_session_maker()
    location_repository = get_location_repository(session_maker=session_maker)
    crop_repository = get_crop_repository(session_maker=session_maker)
    cds_api = get_cds_api()
    past_climate_data_repository = get_past_climate_data_repository(
        session_maker=session_maker,
        cds_api=cds_api,
        location_repository=location_repository,
    )
    crop_yield_data_repository = get_crop_yield_data_repository(
        crop_repository=crop_repository,
        location_repository=location_repository,
        past_climate_data_repository=past_climate_data_repository,
    )
    crop_yield_model_repository = get_crop_yield_model_service(
        past_climate_data_repository=past_climate_data_repository,
        location_repository=location_repository,
        crop_yield_data_repository=crop_yield_data_repository,
        crop_repository=crop_repository,
    )
    async with session_maker() as session:
        await crop_yield_data_repository.download_crop_yield_data(session=session)
        await crop_yield_model_repository.train_and_save_crop_yield_model_for_all_crops(session=session)


if __name__ == "__main__":
    logging_conf.create_logger(config=logging_conf.get_default_conf())
    asyncio.run(main())

import asyncio
import logging

from tesi.climate.di import get_cds_api, get_future_climate_data_repository
from tesi.database.di import get_db_session


async def main():

    logging.basicConfig(level=logging.INFO)

    db_session = await get_db_session()

    cds_api = get_cds_api()

    future_climate_data_repository = get_future_climate_data_repository(
        db_session=db_session, cds_api=cds_api
    )

    future_climate_data_df = (
        await future_climate_data_repository.download_future_climate_data()
    )

    future_climate_data_df.to_csv("training_data/future_climate_data.csv")


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging

import pandas as pd

from tesi.climate.di import (
    get_cds_api,
    get_past_climate_data_repository,
)
from tesi.database.di import get_db_session


async def main():
    logging.basicConfig(level=logging.INFO)

    db_session = await get_db_session()

    cds_api = get_cds_api()

    past_climate_data_repository = get_past_climate_data_repository(
        db_session=db_session, cds_api=cds_api
    )

    new_past_climate_data_csv_path = "training_data/past_climate_data.csv"

    new_past_climate_data_df = pd.read_csv(
        new_past_climate_data_csv_path, index_col=["year", "month"]
    )

    if len(new_past_climate_data_df) > 0:
        await past_climate_data_repository.save_past_climate_data(
            new_past_climate_data_df
        )
    else:
        logging.info(f"No new past climate data to download")


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging
import os
from typing import cast
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

    year_from = 1940
    month_from = 1940

    if os.path.exists(new_past_climate_data_csv_path):
        old_past_climate_data_df = pd.read_csv(
            new_past_climate_data_csv_path, index_col=["year", "month"]
        )
        # Get the last (maximum) year and month directly from the MultiIndex
        max_year_month = old_past_climate_data_df.index.max()

        # Extract year and month from the tuple
        max_year, max_month = max_year_month

        year_from = cast(int, max_year)
        month_from = cast(int, max_month)
        if max_month == 12:
            year_from += 1
            month_from = 1

    new_past_climate_data_df = (
        await past_climate_data_repository.download_new_past_climate_data(
            year_from=year_from,
            month_from=month_from,
            longitude=40.484638,
            latitude=17.225732,
        )
    )

    if len(new_past_climate_data_df) > 0:
        new_past_climate_data_df.to_csv(new_past_climate_data_csv_path)
        await past_climate_data_repository.save_past_climate_data(
            new_past_climate_data_df
        )
    else:
        logging.info(f"No new past climate data to download")


if __name__ == "__main__":
    asyncio.run(main())

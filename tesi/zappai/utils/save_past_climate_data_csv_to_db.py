import asyncio
import logging

import pandas as pd

from tesi.zappai.di import (
    get_cds_api,
    get_location_repository,
    get_past_climate_data_repository,
)
from tesi.database.di import get_db_session
from tesi.zappai.utils import common


async def main():
    logging.basicConfig(level=logging.INFO)

    db_session = await get_db_session()
    location_repository = get_location_repository(db_session=db_session)
    cds_api = get_cds_api()
    past_climate_data_repository = get_past_climate_data_repository(
        db_session=db_session, cds_api=cds_api, location_repository=location_repository
    )

    new_past_climate_data_csv_path = (
        f"training_data/{common.EXAMPLE_LOCATION_NAME}_past_climate_data.csv"
    )

    new_past_climate_data_df = pd.read_csv(
        new_past_climate_data_csv_path, index_col=["year", "month"]
    )

    if len(new_past_climate_data_df) > 0:

        await past_climate_data_repository.__save_past_climate_data(
            location_name=common.EXAMPLE_LOCATION_NAME,
            past_climate_data_df=new_past_climate_data_df,
        )
    else:
        logging.info(f"No new past climate data to download")


if __name__ == "__main__":
    asyncio.run(main())

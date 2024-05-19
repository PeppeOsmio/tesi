import logging
import os
from geoalchemy2 import Geography
import pandas as pd
from asgiref.sync import sync_to_async
from tesi.models import ClimateData
from tesi.utility_scripts import crops_data, future_climate_data
from sqlalchemy.ext.asyncio import AsyncSession


class FuturePredictionsRepository:
    def __init__(self, db_session: AsyncSession, predictions_folder: str) -> None:
        self.predictions_folder = predictions_folder
        self.db_session = db_session

    @sync_to_async
    async def load_climate_data_into_db(self):

        @sync_to_async
        def func():
            return crops_data.download_crops_yield_data()

        crops_df = await func()
        async with self.db_session as session:
            processed = 0
            STEP = 100
            total = len(crops_df)
            while processed < total:
                rows = crops_df[processed : processed + STEP]
                for i, row in rows.iterrows():
                    climate_data = ClimateData(
                        coordinates=f'POINT({row["latitude"], row["longitude"]})',
                        month=row["month"]
                    )

        return pd.DataFrame()

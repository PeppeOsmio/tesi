import logging
import os
from geoalchemy2 import Geography
import pandas as pd
from asgiref.sync import sync_to_async
from tesi.models import FutureClimateData
from tesi.utility_scripts import crops_data, future_climate_data
from sqlalchemy.ext.asyncio import AsyncSession


class FuturePredictionsRepository:
    def __init__(self, db_session: AsyncSession, training_data_folder: str) -> None:
        self.training_data_folder = training_data_folder
        self.db_session = db_session

    async def load_future_climate_data_into_db(self):

        @sync_to_async
        def func():
            return pd.read_csv(os.path.join(self.training_data_folder, "future_climate_data.csv"))

        future_climate_df = await func()
        async with self.db_session as session:
            processed = 0
            STEP = 100
            total = len(future_climate_df)
            while processed < total:
                rows = future_climate_df[processed : processed + STEP]
                for i, row in rows.iterrows():
                    future_climate_data = FutureClimateData(
                        coordinates=f'POINT({row["latitude"], row["longitude"]})',
                        year=row["year"],
                        month=row["month"],
                        precipitations=row["precipitations"],
                        surface_temperature=row["surface_temperature"]
                    )
                    session.add(future_climate_data)
                processed += len(rows)
            await session.commit()

    async def get_future_predictions_for

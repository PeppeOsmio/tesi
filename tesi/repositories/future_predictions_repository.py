import logging
import os
import pandas as pd
from asgiref.sync import sync_to_async


class FuturePredictionsRepository:
    def __init__(self, predictions_folder: str) -> None:
        self.predictions_folder = predictions_folder

    @sync_to_async
    def load_predictions_df(self) -> pd.DataFrame:
        precipitations_csv = os.path.join(self.predictions_folder, "precipitations.csv")
        temperature_at_surface_csv = os.path.join(self.predictions_folder, "temperature_at_surface.csv")

        logging.info(f"Loading {precipitations_csv}")
        precipitations_df = pd.read_csv(
            os.path.join(self.predictions_folder, "precipitations.csv")
        )

        logging.info(f"Loading {temperature_at_surface_csv}")
        temperature_at_surface_df = pd.read_csv(
            os.path.join(self.predictions_folder, "temperature_at_surface.csv")
        )

        print(len(precipitations_df))
        print(len(temperature_at_surface_df))
        return pd.DataFrame()

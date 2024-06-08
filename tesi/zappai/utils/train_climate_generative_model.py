import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import logging
import os
from typing import cast
from uuid import UUID
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.src.layers import LSTM, Dense
from keras.src.models import Sequential
from sklearn.model_selection import train_test_split
from tesi.zappai.exceptions import LocationNotFoundError
from tesi.zappai.repositories.dtos import FutureClimateDataDTO, ClimateDataDTO
from tesi.zappai.repositories import copernicus_data_store_api
from tesi.zappai.di import (
    get_location_repository,
    get_session_maker,
    get_cds_api,
    get_past_climate_data_repository,
    get_future_climate_data_repository,
)
from tesi.zappai.repositories.future_climate_data_repository import (
    FutureClimateDataRepository,
)
from tesi.zappai.repositories.location_repository import LocationRepository
from tesi.zappai.repositories.past_climate_data_repository import (
    PastClimateDataRepository,
)
from tesi.zappai.utils import common
import joblib

CLIMATE_MODELS_DIR = "data/ml_models/"
CLIMATE_GENERATIVE_MODEL_FILEPATH = os.path.join(
    CLIMATE_MODELS_DIR, "climate_generative_model.pkl"
)
CLIMATE_X_SCALER_FILEPATH = os.path.join(CLIMATE_MODELS_DIR, "climate_x_scaler.pkl")
CLIMATE_Y_SCALER_FILEPATH = os.path.join(CLIMATE_MODELS_DIR, "climate_y_scaler.pkl")

_TARGET = list(
    copernicus_data_store_api.ERA5_VARIABLES - copernicus_data_store_api.CMIP5_VARIABLES
)
_FEATURES = list(copernicus_data_store_api.ERA5_VARIABLES)


class ClimateGenerativeModelRepository:
    def __init__(self) -> None:
        pass

    def __format_data(
        self, seq_length: int, x_train_scaled: np.ndarray, y_train_scaled: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        x_train_scaled_with_past_months = []
        y_train_scaled_for_model = []
        for i in range(len(x_train_scaled) - seq_length):
            past_months_sequence = x_train_scaled[i : i + seq_length]
            x_train_scaled_with_past_months.append(past_months_sequence)
            y_train_scaled_for_model.append(y_train_scaled[i + seq_length])
        return np.array(x_train_scaled_with_past_months), np.array(
            y_train_scaled_for_model
        )

    def __generate_model(self, seq_length: int) -> Sequential:
        model = Sequential()
        model.add(LSTM(50, input_shape=(seq_length, len(_FEATURES))))
        model.add(Dense(25, activation="relu"))
        model.add(Dense(len(_TARGET)))

        model.compile(optimizer="adam", loss="mean_squared_error", metrics=["accuracy"])
        return model

    def __train_model(
        self,
        past_climate_data_df: pd.DataFrame,
        seq_length: int,
    ) -> tuple[Sequential, MinMaxScaler, MinMaxScaler]:

        x = past_climate_data_df[_FEATURES]
        y = past_climate_data_df[_TARGET]

        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=0.2, shuffle=False
        )

        # Normalize the data
        x_scaler = MinMaxScaler(feature_range=(0, 1))
        y_scaler = MinMaxScaler(feature_range=(0, 1))
        x_train_scaled = x_scaler.fit_transform(x_train)
        x_test_scaled = x_scaler.transform(x_test)
        y_train_scaled = y_scaler.fit_transform(y_train)
        y_test_scaled = y_scaler.transform(y_test)

        x_train_scaled_with_months, y_train_scaled_for_model = self.__format_data(
            seq_length=seq_length,
            x_train_scaled=x_train_scaled,
            y_train_scaled=y_train_scaled,
        )
        model = self.__generate_model(seq_length=seq_length)
        model.fit(x_train_scaled_with_months, y_train_scaled_for_model, epochs=50)
        return model, x_scaler, y_scaler

    async def create_model_for_location(
        self,
        location_repository: LocationRepository,
        past_climate_data_repository: PastClimateDataRepository,
        location_id: UUID,
    ):
        """Creates as Sequential model

        Args:
            location_repository (LocationRepository):
            past_climate_data_repository (PastClimateDataRepository):
            location_id (UUID):

        Raises:
            LocationNotFoundError:
        """
        location = await location_repository.get_location_by_id(location_id=location_id)
        if location is None:
            raise LocationNotFoundError()

        past_climate_data_df = ClimateDataDTO.from_list_to_dataframe(
            await past_climate_data_repository.get_past_climate_data_for_location(
                location_id=location.id
            )
        )

        SEQ_LENGTH = 12

        model = self.__generate_model(seq_length=SEQ_LENGTH)
        model, x_scaler, y_scaler = self.__train_model(
            past_climate_data_df=past_climate_data_df,
            seq_length=SEQ_LENGTH,
        )

        def dump_func():
            os.makedirs(CLIMATE_MODELS_DIR, exist_ok=True)
            joblib.dump(value=model, filename=CLIMATE_GENERATIVE_MODEL_FILEPATH)
            joblib.dump(value=x_scaler, filename=CLIMATE_X_SCALER_FILEPATH)
            joblib.dump(value=y_scaler, filename=CLIMATE_Y_SCALER_FILEPATH)

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(executor=pool, func=dump_func)

    def __generate_climate_data(
        self,
        future_climate_data_df: pd.DataFrame,
        seed_past_12_months_data: pd.DataFrame,
        x_scaler: MinMaxScaler,
        y_scaler: MinMaxScaler,
        model: Sequential,
    ) -> list[np.ndarray]:
        """Generates future climate data from the latest available past climate data

        Args:
            future_climate_data_df (pd.DataFrame):
            seed_past_12_months_data (pd.DataFrame):
            x_scaler (MinMaxScaler):
            y_scaler (MinMaxScaler):
            model (Sequential):

        Returns:
            list[np.ndarray]:
        """
        generated_data: list[np.ndarray] = []
        current_12_months_data = seed_past_12_months_data
        future_climate_data_array = future_climate_data_df.to_numpy()
        for _, future_climate_data in enumerate(future_climate_data_array):
            current_12_months_data_scaled = x_scaler.transform(current_12_months_data)
            era5_not_in_cmip5_variables_prediction = model.predict(
                np.array([current_12_months_data_scaled])
            )[0]

            transformed_era5_not_in_cmip5_variables_prediction = (
                y_scaler.inverse_transform(
                    np.array([era5_not_in_cmip5_variables_prediction])
                )[0]
            )

            # contains the next months's data, which is combined  rom prediction and CMIP5 data
            next_month_data_prediction = np.append(
                transformed_era5_not_in_cmip5_variables_prediction,
                future_climate_data,
                axis=0,
            )

            generated_data.append(next_month_data_prediction)

            # remove the first month of data and push the next month's generated data
            current_12_months_data = np.append(
                current_12_months_data[1:],
                [next_month_data_prediction],
                axis=0,
            )
        return generated_data

    async def test_model(
        self,
        past_climate_data_repository: PastClimateDataRepository,
        future_climate_data_repository: FutureClimateDataRepository,
        location_repository: LocationRepository,
        location_id: UUID,
    ):

        def load_func() -> tuple[Sequential, MinMaxScaler, MinMaxScaler]:
            model = cast(
                Sequential, joblib.load(filename=CLIMATE_GENERATIVE_MODEL_FILEPATH)
            )
            x_scaler = cast(
                MinMaxScaler, joblib.load(filename=CLIMATE_X_SCALER_FILEPATH)
            )
            y_scaler = cast(
                MinMaxScaler, joblib.load(filename=CLIMATE_Y_SCALER_FILEPATH)
            )
            return model, x_scaler, y_scaler

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            model, x_scaler, y_scaler = await loop.run_in_executor(
                executor=pool, func=load_func
            )

        location = await location_repository.get_location_by_id(location_id)
        if location is None:
            raise LocationNotFoundError()

        last_12_months_seed_data = ClimateDataDTO.from_list_to_dataframe(
            await past_climate_data_repository.get_past_climate_data_of_location_of_previous_12_months(
                location_id=location_id
            )
        )
        last_12_months_seed_data = last_12_months_seed_data[_FEATURES]

        index = last_12_months_seed_data.index[-1]
        start_year, start_month = index
        start_year = cast(int, start_year)
        start_month = cast(int, start_month)

        future_climate_data_df = FutureClimateDataDTO.from_list_to_dataframe(
            await future_climate_data_repository.get_future_climate_data_for_nearest_coordinates(
                longitude=location.longitude, latitude=location.latitude
            )
        )
        future_climate_data_df = future_climate_data_df[
            list(copernicus_data_store_api.CMIP5_VARIABLES)
        ]
        future_climate_data_df = future_climate_data_df[
            (future_climate_data_df.index.get_level_values("year") > start_year)
            | (
                (future_climate_data_df.index.get_level_values("year") == start_year)
                & (future_climate_data_df.index.get_level_values("month") > start_month)
            )
        ]

        data = self.__generate_climate_data(
            future_climate_data_df=future_climate_data_df,
            seed_past_12_months_data=last_12_months_seed_data,
            x_scaler=x_scaler,
            y_scaler=y_scaler,
            model=model,
        )

        print(data)

async def main():
    session_maker = get_session_maker()
    cds_api = get_cds_api()
    location_repository = get_location_repository(session_maker=session_maker)
    past_climate_data_repository = get_past_climate_data_repository(
        session_maker=session_maker,
        cds_api=cds_api,
        location_repository=location_repository,
    )
    future_climate_data_repository = get_future_climate_data_repository(
        session_maker=session_maker, cds_api=cds_api
    )

    location = await location_repository.get_location_by_country_and_name(
        country=common.EXAMPLE_LOCATION_COUNTRY, name=common.EXAMPLE_LOCATION_NAME
    )
    if location is None:
        location = await location_repository.create_location(
            country=common.EXAMPLE_LOCATION_COUNTRY,
            name=common.EXAMPLE_LOCATION_NAME,
            longitude=common.EXAMPLE_LONGITUDE,
            latitude=common.EXAMPLE_LATITUDE,
        )

    climate_generative_model_repository = ClimateGenerativeModelRepository()

    await climate_generative_model_repository.create_model_for_location(
        location_repository=location_repository,
        past_climate_data_repository=past_climate_data_repository,
        location_id=location.id,
    )
    await climate_generative_model_repository.test_model(
        past_climate_data_repository=past_climate_data_repository,
        future_climate_data_repository=future_climate_data_repository,
        location_repository=location_repository,
        location_id=location.id,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

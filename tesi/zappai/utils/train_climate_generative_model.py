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
    copernicus_data_store_api.ERA5_VARIABLES
    - copernicus_data_store_api.CMIP5_VARIABLES
)
_FEATURES = list(copernicus_data_store_api.ERA5_VARIABLES)

def inverse_transform_generated_data(scaler, data):
    return scaler.inverse_transform(data)


def combine_with_fixed_features(seed_data, generated_data):
    # Placeholder function: implement according to your specific requirements
    return np.array(generated_data)


def format_data(
    seq_length: int, x_train_scaled: np.ndarray, y_train_scaled: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    x_train_scaled_with_past_months = []
    y_train_scaled_for_model = []
    for i in range(len(x_train_scaled) - seq_length):
        past_months_sequence = x_train_scaled[i : i + seq_length]
        x_train_scaled_with_past_months.append(past_months_sequence)
        y_train_scaled_for_model.append(y_train_scaled[i + seq_length])
    return np.array(x_train_scaled_with_past_months), np.array(y_train_scaled_for_model)


def generate_data(data_length: int, model: Sequential):
    pass


def generate_model(seq_length: int) -> Sequential:
    model = Sequential()
    model.add(LSTM(50, input_shape=(seq_length, len(_FEATURES))))
    model.add(Dense(25, activation="relu"))
    model.add(Dense(len(_TARGET)))

    model.compile(optimizer="adam", loss="mean_squared_error", metrics=["accuracy"])
    return model


def train_model(
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

    x_train_scaled_with_months, y_train_scaled_for_model = format_data(
        seq_length=seq_length,
        x_train_scaled=x_train_scaled,
        y_train_scaled=y_train_scaled,
    )
    model = generate_model(seq_length=seq_length)
    model.fit(x_train_scaled_with_months, y_train_scaled_for_model, epochs=50)
    return model, x_scaler, y_scaler


async def create_and_train_climate_generative_model_for_location(
    location_repository: LocationRepository,
    past_climate_data_repository: PastClimateDataRepository,
    future_climate_data_repository: FutureClimateDataRepository,
    location_id: UUID,
):
    # Load and preprocess data

    location = await location_repository.get_location_by_id(location_id=location_id)
    if location is None:
        raise LocationNotFoundError()

    past_climate_data_df = ClimateDataDTO.from_list_to_dataframe(
        await past_climate_data_repository.get_past_climate_data_for_location(
            location_id=location.id
        )
    )

    SEQ_LENGTH = 12

    model = generate_model(seq_length=SEQ_LENGTH)
    model, x_scaler, y_scaler = train_model(
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


async def test_model(
    past_climate_data_repository: PastClimateDataRepository,
    future_climate_data_repository: FutureClimateDataRepository,
    location_repository: LocationRepository,
    location_id: UUID,
):

    location = await location_repository.get_location_by_id(location_id)
    if location is None:
        raise LocationNotFoundError()

    seed_data = ClimateDataDTO.from_list_to_dataframe(
        await past_climate_data_repository.get_past_climate_data_of_location_of_previous_12_months(
            location_id=location_id
        )
    )
    
    index = seed_data.index[-1]
    start_year, start_month = index
    start_year = cast(int, start_year)
    start_month = cast(int, start_month)

    def load_func() -> tuple[Sequential, MinMaxScaler, MinMaxScaler]:
        model = cast(
            Sequential, joblib.load(filename=CLIMATE_GENERATIVE_MODEL_FILEPATH)
        )
        x_scaler = cast(MinMaxScaler, joblib.load(filename=CLIMATE_X_SCALER_FILEPATH))
        y_scaler = cast(MinMaxScaler, joblib.load(filename=CLIMATE_Y_SCALER_FILEPATH))
        return model, x_scaler, y_scaler

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        model, x_scaler, y_scaler = await loop.run_in_executor(
            executor=pool, func=load_func
        )

    seed_data = seed_data[_FEATURES]

    scaled_seed_data = x_scaler.transform(seed_data)

    future_climate_data_df = FutureClimateDataDTO.from_list_to_dataframe(
        await future_climate_data_repository.get_future_climate_data_for_nearest_coordinates(
            longitude=location.longitude, latitude=location.latitude
        )
    )

    future_climate_data_df = future_climate_data_df[list(copernicus_data_store_api.CMIP5_VARIABLES)]

    future_climate_data_df = future_climate_data_df[
        (future_climate_data_df.index.get_level_values("year") > start_year)
        & (future_climate_data_df.index.get_level_values("month") > start_month)
    ]
    

    future_climate_data_array = future_climate_data_df.to_numpy()

    print(future_climate_data_df.columns)

    generated_data = []
    current_step = scaled_seed_data

    # TODO proper scaling pls

    for _, future_climate_data in enumerate(future_climate_data_array):
        prediction = cast(np.ndarray, model.predict(np.array([current_step]))[0])
        transformed_prediction = y_scaler.inverse_transform(np.array([prediction]))[0]
        print("future_climate_data: ")
        print(future_climate_data.shape)
        print("transformed_prediction: ")
        print(transformed_prediction.shape)
        enriched_prediction = np.append(transformed_prediction, future_climate_data, axis=0)
        print_dict: dict[str, float] = {}
        for i, feature in enumerate(_FEATURES):
            print_dict.update({feature: enriched_prediction[i]})
        print(print_dict)
        generated_data.append(enriched_prediction)
        current_step = np.append(
            current_step[:-1],
            [enriched_prediction],
            axis=0,
        )

    generated_combined = combine_with_fixed_features(seed_data, generated_data)

    generated_data_original = inverse_transform_generated_data(
        x_scaler, generated_combined
    )


async def main():
    # Load and preprocess data

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

    await create_and_train_climate_generative_model_for_location(
        location_repository=location_repository,
        past_climate_data_repository=past_climate_data_repository,
        future_climate_data_repository=future_climate_data_repository,
        location_id=location.id,
    )
    await test_model(
        past_climate_data_repository=past_climate_data_repository,
        future_climate_data_repository=future_climate_data_repository,
        location_repository=location_repository,
        location_id=location.id,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

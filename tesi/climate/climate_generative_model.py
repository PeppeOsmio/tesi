import os
from asgiref.sync import async_to_sync
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.src.layers import LSTM, Dense
from keras.src.models import Sequential
from sklearn.model_selection import train_test_split
from tesi.climate.dtos import FutureClimateDataDTO, PastClimateDataDTO
from tesi.climate.utils import copernicus_data_store_api
from tesi.climate.di import (
    get_db_session,
    get_cds_api,
    get_past_climate_data_repository,
    get_future_climate_data_repository,
)


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


def generate_model(features: int, target: int, seq_length: int) -> Sequential:
    model = Sequential()
    model.add(LSTM(50, input_shape=(seq_length, features)))
    model.add(Dense(25, activation="relu"))
    model.add(Dense(target))

    model.compile(optimizer="adam", loss="mean_squared_error", metrics=["accuracy"])
    return model


def train_model(
    features: list[str],
    target: list[str],
    past_climate_data_df: pd.DataFrame,
    seq_length: int,
) -> tuple[Sequential, MinMaxScaler, MinMaxScaler]:
    x = past_climate_data_df[features]
    y = past_climate_data_df[target]

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
    model = generate_model(
        features=len(features), target=len(target), seq_length=seq_length
    )
    model.fit(x_train_scaled_with_months, y_train_scaled_for_model, epochs=50)
    return model, x_scaler, y_scaler


def main():
    # Load and preprocess data

    TARANTO_LONGITUDE, TARANTO_LATITUDE = 40.484638, 17.225732

    target = list(
        copernicus_data_store_api.ERA5_RESULT_COLUMNS
        - copernicus_data_store_api.CMIP5_RESULT_COLUMNS
    )
    features = list(copernicus_data_store_api.ERA5_RESULT_COLUMNS)

    @async_to_sync
    async def func_db():
        return await get_db_session()

    db_session = func_db()

    cds_api = get_cds_api()

    past_training_data_csv_path = "training_data/past_climate_data.csv"
    past_climate_data_repository = get_past_climate_data_repository(
        db_session=db_session, cds_api=cds_api
    )

    if os.path.exists(past_training_data_csv_path):
        past_climate_data_df = pd.read_csv(past_training_data_csv_path, index_col=["year", "month"])
    else:
        past_climate_data_df = PastClimateDataDTO.from_list_to_dataframe(
            past_climate_data_repository.get_past_climate_data(
                longitude=TARANTO_LONGITUDE, latitude=TARANTO_LATITUDE
            )
        )
        past_climate_data_df.to_csv(past_training_data_csv_path)

    future_climate_data_csv_path = "training_data/future_climate_data.csv"
    future_climate_data_repository = get_future_climate_data_repository(
        db_session=db_session, cds_api=cds_api
    )
    if os.path.exists(future_climate_data_csv_path):
        future_climate_data_df = pd.read_csv(future_climate_data_csv_path, index_col=["year", "month"])
    else:
        future_climate_data_df = (
            future_climate_data_repository.download_future_climate_data()
        )
        future_climate_data_df.to_csv(future_climate_data_csv_path)
    future_climate_data_repository.save_future_climate_data(future_climate_data_df)

    SEQ_LENGTH = 12

    model = generate_model(
        features=len(features), target=len(target), seq_length=SEQ_LENGTH
    )
    model, x_scaler, y_scaler = train_model(
        features=features,
        target=target,
        past_climate_data_df=past_climate_data_df,
        seq_length=SEQ_LENGTH,
    )

    seed_data = PastClimateDataDTO.from_list_to_dataframe(
        past_climate_data_repository.get_past_climate_data_of_last_12_months(
            longitude=TARANTO_LONGITUDE, latitude=TARANTO_LATITUDE
        )
    )

    scaled_seed_data = x_scaler.transform(seed_data)
    print(scaled_seed_data)
    return
    generated_data = []
    current_step = scaled_seed_data

    for _ in range(100):
        prediction = model.predict(np.array([current_step]))[0]
        generated_data.append(prediction)
        print(generated_data)
        return
        current_step = np.append(
            current_step[1:],
            [np.concatenate((current_step[-1, : -len(target)], prediction))],
            axis=0,
        )

    generated_combined = combine_with_fixed_features(seed_data, generated_data)

    generated_data_original = inverse_transform_generated_data(
        x_scaler, generated_combined
    )
    print(generated_data_original)


if __name__ == "__main__":
    main()

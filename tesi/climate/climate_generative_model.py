import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.src.layers import LSTM, Dense
from keras.src.models import Sequential
from sklearn.model_selection import train_test_split


def inverse_transform_generated_data(scaler, data):
    return scaler.inverse_transform(data)


def combine_with_fixed_features(seed_data, generated_data):
    # Placeholder function: implement according to your specific requirements
    return np.array(generated_data)


def generate_model(features: int, target: int, seq_length: int) -> Sequential:
    model = Sequential()
    model.add(LSTM(50, input_shape=(seq_length, features)))
    model.add(Dense(25, activation="relu"))
    model.add(Dense(target))

    model.compile(optimizer="adam", loss="mean_squared_error", metrics=["accuracy"])
    return model


def format_data(
    seq_length: int, x_train_scaled: np.ndarray, y_train_scaled: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    x_train_scaled_with_past_months = []
    for i in range(len(x_train_scaled) - seq_length):
        past_months_sequence = x_train_scaled[i : i + seq_length]
        x_train_scaled_with_past_months.append(past_months_sequence)
    y_train_scaled_for_model = y_train_scaled[seq_length:]
    return np.array(x_train_scaled_with_past_months), y_train_scaled_for_model


def generate_data(data_length: int, model: Sequential):
    pass


def train_model(
    model: Sequential,
    features: list[str],
    target: list[str],
    past_climate_data: pd.DataFrame,
    seq_length: int,
) -> tuple[MinMaxScaler, MinMaxScaler]:
    x = past_climate_data[features]
    y = past_climate_data[target]

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
    model.fit(x_train_scaled_with_months, y_train_scaled_for_model, epochs=50)
    return x_scaler, y_scaler

def main():
    # Load and preprocess data
    features = [
        # "year",
        # "month",
        # "longitude",
        # "latitude",
        "surface_temperature",
        "total_precipitations",
        "surface_net_solar_radiation",
        "surface_pressure",
        "volumetric_soil_water_layer_1",
    ]
    target = [
        "surface_net_solar_radiation",
        "surface_pressure",
        "volumetric_soil_water_layer_1",
    ]
    past_climate_data = pd.read_csv("training_data/past_climate_data.csv")

    SEQ_LENGTH = 12

    model = generate_model(
        features=len(features), target=len(target), seq_length=SEQ_LENGTH
    )
    x_scaler, y_scaler = train_model(
        model=model,
        features=features,
        target=target,
        past_climate_data=past_climate_data,
        seq_length=SEQ_LENGTH,
    )

    seed_data = x_train_scaled_with_months[-1]
    scaled_seed_data = x_scaler.transform(seed_data)
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

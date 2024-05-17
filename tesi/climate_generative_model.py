import logging
import os

from matplotlib import pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from tesi import copernicus_data_store_api

TARANTO_LAT = 40.464361
TARANTO_LON = 17.247030


def get_climate_data() -> pd.DataFrame:
    if not os.path.exists("data/taranto.csv"):
        climate_data = copernicus_data_store_api.get_climate_data_since_1940_sync(
            lat=TARANTO_LAT, lon=TARANTO_LON
        )
        climate_data.to_csv("data/taranto.csv")
    else:
        climate_data = pd.read_csv(
            "data/taranto.csv", parse_dates=["time"], index_col=["time"]
        )
    return climate_data


def get_next_month_column(column: str) -> str:
    return f"{column}_delta_next_month"


def get_next_month_columns(base_features: list[str]) -> list[str]:
    return [
        get_next_month_column(column)
        for column in base_features
    ]


def get_lagged_column(column: str, lag: int) -> str:
    return f"{column}_delta_{lag+1}_months_ago"

def get_lagged_features(NUM_LAGS: int, base_features:list[str]) -> dict[str, list[str]]:
    lagged_features_dict: dict[str, list[str]] = {}
    for i, base_feature in enumerate(base_features):
        lagged_features: list[str] = []
        for j in range(NUM_LAGS):
            lagged_features.append(get_lagged_column(column=base_feature, lag=j))
        lagged_features_dict.update({base_feature: lagged_features})
    return lagged_features_dict

def get_next_month_features(base_features: list[str]) -> dict[str, str]:
    return {base_feature: get_next_month_column(base_feature) for base_feature in base_features}

def get_training_data_frame(data: pd.DataFrame, base_features: list[str]) -> pd.DataFrame:
    model_df = data.copy()

    # add lagged delta columns
    NUM_LAGS = 8
    for column in base_features:
        for i in range(NUM_LAGS):
            model_df[get_lagged_column(column=column, lag=i)] = model_df[column].diff(
                i + 1
            )
    model_df = model_df[NUM_LAGS:]

    # add next month delta column
    for column in base_features:
        model_df[get_next_month_column(column=column)] = model_df[column].diff(-1)
    model_df = model_df[:-1]

    ordered_columns: list[str] = ["year", "month"]
    # reorder columns
    for column in base_features:
        ordered_columns.append(column)
        for i in range(NUM_LAGS):
            ordered_columns.append(get_lagged_column(column=column, lag=i))
        ordered_columns.append(get_next_month_column(column=column))
    model_df = model_df[ordered_columns]

    months = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ]

    for i, month in enumerate(months, start=1):
        model_df[f"is_{month}"] = (model_df["month"] == i).astype(int)

    model_df.to_csv("data/taranto_ml.csv")
    return model_df


def plot(df: pd.DataFrame):

    # Create subplots
    fig, ax1 = plt.subplots()

    past_year = 2022
    new_year = 2023

    past_df = df[f"{past_year}-01":f"{past_year}-12"]
    new_df = df[f"{new_year}-01":f"{new_year}-12"]

    # Plot 2m_temperature and 10m_wind_speed on the primary y-axis
    color_past = "tab:blue"
    color_new = "tab:red"

    ax1.set_xlabel("Time")
    ax1.set_ylabel("2m_temperature (K)")
    ax1.plot(
        past_df["month"],
        past_df["2m_temperature"],
        color=color_past,
        label="2m_temperature",
    )
    ax1.plot(
        new_df["month"],
        new_df["2m_temperature"],
        color=color_new,
        label="2m_temperature",
    )
    ax1.tick_params(axis="y")

    fig.tight_layout()  # to prevent the labels from overlapping

    # Show the plot
    plt.title("2m Temperature Over Time")
    plt.show()


def main():
    logging.info("Fetching data...")
    data = get_climate_data()

    base_features = [
        "2m_temperature",
        "total_precipitation",
        "10m_wind_speed",
        "precipitation_type",
        "surface_net_solar_radiation",
        "snow_depth",
        "surface_pressure",
        "volumetric_soil_water_layer_1",
    ]

    logging.info("Creating model dataset...")
    model_data = get_training_data_frame(data, base_features)

    logging.info("Training model...")
    x = model_data.drop(columns=["year", "month", *get_next_month_columns(base_features)])
    y = model_data[get_next_month_columns(base_features)]

    print(f"len(x): {len(x)}")
    print(f"len(y): {len(y)}")

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=13
    )

    print(f"len(x_train): {len(x_train)}")
    print(f"len(y_train): {len(y_train)}")

    print(x_train)
    print(y_train)

    # model = RandomForestRegressor(n_estimators=100, random_state=13)
    model = LinearRegression()
    model.fit(x_train, y_train)

    logging.info("Testing model...")
    y_pred = model.predict(x_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"mse: {mse}")
    print(f"r2: {r2}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

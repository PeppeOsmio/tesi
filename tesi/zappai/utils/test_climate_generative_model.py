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
from tesi.zappai.repositories.climate_generative_model_repository import (
    ClimateGenerativeModelRepository,
)
from tesi.zappai.repositories.dtos import FutureClimateDataDTO, ClimateDataDTO
from tesi.zappai.repositories import copernicus_data_store_api
from tesi.zappai.di import (
    get_climate_generative_model_repository,
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
import matplotlib.pyplot as plt


def plot_climate_data(past_df: pd.DataFrame, generated_df: pd.DataFrame):
    # Combine data for plotting
    past_df["type"] = "Past"
    generated_df["type"] = "Generated"

    past_df = past_df.reset_index()
    generated_df = generated_df.reset_index()

    combined_df = pd.concat([past_df, generated_df])

    # Create a single datetime column for proper plotting
    combined_df["date"] = pd.to_datetime(combined_df[["year", "month"]].assign(day=1))

    # Plot temperature
    plt.figure(figsize=(12, 6))
    plt.plot(
        combined_df["date"],
        combined_df["2m_dewpoint_temperature"],
        label="2m_dewpoint_temperature",
    )

    plt.xlabel("Date")
    plt.ylabel("2m_dewpoint_temperature (K)")
    plt.title("Temperature Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()

    return

    # Plot rainfall
    plt.figure(figsize=(12, 6))
    for data_type in combined_df["type"].unique():
        subset = combined_df[combined_df["type"] == data_type]
        plt.plot(subset["date"], subset["rainfall"], label=f"{data_type} Rainfall")

    plt.xlabel("Date")
    plt.ylabel("Rainfall (mm)")
    plt.title("Rainfall Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()


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

    climate_generative_model_repository = get_climate_generative_model_repository(
        session_maker=session_maker,
        location_repository=location_repository,
        past_climate_data_repository=past_climate_data_repository,
        future_climate_data_repository=future_climate_data_repository,
    )

    await climate_generative_model_repository.delete_climate_generative_model(
        location.id
    )

    climate_generative_model = await climate_generative_model_repository.get_climate_generative_model_by_location_id(
        location.id
    )
    if climate_generative_model is None:
        await climate_generative_model_repository.create_model_for_location(
            location_id=location.id,
        )
    generated_data = await climate_generative_model_repository.generate_climate_data_from_last_past_climate_data(
        location_id=location.id,
    )
    past_climate_data = ClimateDataDTO.from_list_to_dataframe(
        await past_climate_data_repository.get_past_climate_data(location.id)
    )

    print(past_climate_data["2m_temperature"])
    print(generated_data["2m_temperature"])

    past_climate_data.to_csv("past.csv")
    generated_data.to_csv("future.csv")

    plot_climate_data(past_df=past_climate_data, generated_df=generated_data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

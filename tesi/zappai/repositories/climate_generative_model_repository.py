import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import logging
import os
from typing import Any, cast
from uuid import UUID
from io import BytesIO
import uuid
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.src.layers import LSTM, Dense
from keras.src.models import Sequential
from sklearn.model_selection import train_test_split
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tesi.zappai.exceptions import (
    ClimateGenerativeModelNotFoundError,
    LocationNotFoundError,
)
from tesi.zappai.models import ClimateGenerativeModel
from tesi.zappai.repositories.dtos import (
    ClimateGenerativeModelDTO,
    FutureClimateDataDTO,
    ClimateDataDTO,
)
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


class ClimateGenerativeModelRepository:
    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        location_repository: LocationRepository,
        past_climate_data_repository: PastClimateDataRepository,
        future_climate_data_repository: FutureClimateDataRepository,
    ) -> None:
        self.session_maker = session_maker
        self.location_repository = location_repository
        self.past_climate_data_repository = past_climate_data_repository
        self.future_climate_data_repository = future_climate_data_repository

    _TARGET = list(
        copernicus_data_store_api.ERA5_VARIABLES
        - copernicus_data_store_api.CMIP5_VARIABLES
    )
    _FEATURES = list(copernicus_data_store_api.ERA5_VARIABLES)

    def __bytes_to_object(self, bts: bytes) -> Any:
        bytes_io = BytesIO(initial_bytes=bts)
        return joblib.load(filename=bytes_io)

    def __object_to_bytes(self, obj: Any) -> bytes:
        bytes_io = BytesIO()
        joblib.dump(value=obj, filename=bytes_io)
        bytes_io.seek(0)
        return bytes_io.read()

    def __format_data(
        self, seq_length: int, x_scaled: np.ndarray, y_scaled: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        x_train_scaled_with_past_months = []
        y_train_scaled_for_model = []
        for i in range(len(x_scaled) - seq_length):
            past_months_sequence = x_scaled[i : i + seq_length]
            x_train_scaled_with_past_months.append(past_months_sequence)
            y_train_scaled_for_model.append(y_scaled[i + seq_length])
        return np.array(x_train_scaled_with_past_months), np.array(
            y_train_scaled_for_model
        )

    def __generate_model(self, seq_length: int) -> Sequential:
        model = Sequential()
        model.add(LSTM(50, input_shape=(seq_length, len(self._FEATURES))))
        model.add(Dense(25, activation="relu"))
        model.add(Dense(len(self._TARGET)))

        model.compile(optimizer="adam", loss="mean_squared_error", metrics=["accuracy"])
        return model

    def __train_model(
        self,
        past_climate_data_df: pd.DataFrame,
    ) -> tuple[Sequential, MinMaxScaler, MinMaxScaler]:

        x = past_climate_data_df[self._FEATURES].to_numpy()
        y = past_climate_data_df[self._TARGET].to_numpy()

        # x_train, x_test, y_train, y_test = train_test_split(
        #     x, y, test_size=0.2, shuffle=False
        # )

        # x_scaler = MinMaxScaler(feature_range=(0, 1))
        # y_scaler = MinMaxScaler(feature_range=(0, 1))
        # x_train_scaled = x_scaler.fit_transform(x_train)
        # x_test_scaled = x_scaler.transform(x_test)
        # y_train_scaled = y_scaler.fit_transform(y_train)
        # y_test_scaled = y_scaler.transform(y_test)

        x_scaler = MinMaxScaler(feature_range=(0, 1))
        y_scaler = MinMaxScaler(feature_range=(0, 1))

        x_scaled = x_scaler.fit_transform(x)
        y_scaled = y_scaler.fit_transform(y)

        x_scaled_with_months, y_scaled_for_model = self.__format_data(
            seq_length=12,
            x_scaled=x_scaled,
            y_scaled=y_scaled,
        )
        model = self.__generate_model(seq_length=12)
        model.fit(x_scaled_with_months, y_scaled_for_model, epochs=50)
        return model, x_scaler, y_scaler

    async def create_model_for_location(
        self,
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
        location = await self.location_repository.get_location_by_id(
            location_id=location_id
        )
        if location is None:
            raise LocationNotFoundError()

        past_climate_data_df = ClimateDataDTO.from_list_to_dataframe(
            await self.past_climate_data_repository.get_past_climate_data_for_location(
                location_id=location.id
            )
        )

        # train in thread
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            model, x_scaler, y_scaler = await loop.run_in_executor(
                executor=pool,
                func=lambda: self.__train_model(
                    past_climate_data_df=past_climate_data_df,
                ),
            )

        await self.__save_climate_generative_model(
            location_id=location_id, model=model, x_scaler=x_scaler, y_scaler=y_scaler
        )

    async def get_climate_generative_model_by_location_id(
        self, location_id: UUID
    ) -> ClimateGenerativeModelDTO | None:
        async with self.session_maker() as session:
            stmt = select(ClimateGenerativeModel).where(
                ClimateGenerativeModel.location_id == location_id
            )
            climate_generative_model = await session.scalar(stmt)
        if climate_generative_model is None:
            return None

        return ClimateGenerativeModelDTO(
            id=climate_generative_model.id,
            location_id=location_id,
            model=self.__bytes_to_object(climate_generative_model.model),
            x_scaler=self.__bytes_to_object(climate_generative_model.x_scaler),
            y_scaler=self.__bytes_to_object(climate_generative_model.y_scaler),
        )

    async def __save_climate_generative_model(
        self,
        location_id: UUID,
        model: Sequential,
        x_scaler: MinMaxScaler,
        y_scaler: MinMaxScaler,
    ):
        async with self.session_maker() as session:
            stmt = insert(ClimateGenerativeModel).values(
                id=uuid.uuid4(),
                location_id=location_id,
                model=self.__object_to_bytes(model),
                x_scaler=self.__object_to_bytes(x_scaler),
                y_scaler=self.__object_to_bytes(y_scaler),
            )
            await session.execute(stmt)
            await session.commit()

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

    async def generate_data(
        self,
        location_id: UUID,
    ):
        location = await self.location_repository.get_location_by_id(location_id)
        if location is None:
            raise LocationNotFoundError()

        climate_generative_model = (
            await self.get_climate_generative_model_by_location_id(
                location_id=location_id
            )
        )
        if climate_generative_model is None:
            raise ClimateGenerativeModelNotFoundError()

        last_12_months_seed_data = ClimateDataDTO.from_list_to_dataframe(
            await self.past_climate_data_repository.get_past_climate_data_of_location_of_previous_12_months(
                location_id=location_id
            )
        )
        last_12_months_seed_data = last_12_months_seed_data[self._FEATURES]

        index = last_12_months_seed_data.index[-1]
        start_year, start_month = index
        start_year = cast(int, start_year)
        start_month = cast(int, start_month)

        future_climate_data_df = FutureClimateDataDTO.from_list_to_dataframe(
            await self.future_climate_data_repository.get_future_climate_data_for_nearest_coordinates(
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
            x_scaler=climate_generative_model.x_scaler,
            y_scaler=climate_generative_model.y_scaler,
            model=climate_generative_model.model,
        )

        return

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast
from uuid import UUID
from io import BytesIO
import uuid
from keras.src.losses import mean_squared_error
import numpy as np
import pandas as pd
from keras.src.layers import LSTM, Dense
from keras.src.models import Sequential
from sklearn.preprocessing import StandardScaler
from sqlalchemy import delete, insert, select
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
from tesi.zappai.repositories.future_climate_data_repository import (
    FutureClimateDataRepository,
)
from tesi.zappai.repositories.location_repository import LocationRepository
from tesi.zappai.repositories.past_climate_data_repository import (
    PastClimateDataRepository,
)
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

    _TARGET = copernicus_data_store_api.ERA5_EXCLUSIVE_VARIABLES
    _FEATURES = list(copernicus_data_store_api.ERA5_VARIABLES)

    def __bytes_to_object(self, bts: bytes) -> Any:
        bytes_io = BytesIO(initial_bytes=bts)
        return joblib.load(filename=bytes_io)

    def __object_to_bytes(self, obj: Any) -> bytes:
        bytes_io = BytesIO()
        joblib.dump(value=obj, filename=bytes_io)
        bytes_io.seek(0)
        return bytes_io.read()

    def __get_scalers(
        self, x_train: pd.DataFrame, y_train: pd.DataFrame
    ) -> tuple[StandardScaler, StandardScaler]:
        x_scaler = StandardScaler()
        y_scaler = StandardScaler()

        x_scaler = x_scaler.fit(x_train.to_numpy())
        y_scaler = y_scaler.fit(y_train.to_numpy())

        return x_scaler, y_scaler

    def __format_data(
        self, seq_lenght: int, x_scaled: np.ndarray, y_scaled: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        x_scaled_with_sequences = []
        y_scaled_for_sequences = []
        for i in range(len(x_scaled) - seq_lenght):
            past_months_sequence = x_scaled[i : i + seq_lenght]
            x_scaled_with_sequences.append(past_months_sequence)
            y_scaled_for_sequences.append(y_scaled[i + seq_lenght])
        return np.array(x_scaled_with_sequences), np.array(y_scaled_for_sequences)

    def __train_model(
        self, past_climate_data_df: pd.DataFrame
    ) -> tuple[Sequential, StandardScaler, StandardScaler, float]:

        x = past_climate_data_df[self._FEATURES]
        y = past_climate_data_df[self._TARGET]

        perc_70_x = int(len(x) * 0.7)
        perc_85_x = int(len(x) * 0.85)

        x_train = x[:perc_70_x]
        x_val = x[perc_70_x:perc_85_x]
        x_test = x[perc_85_x:]

        perc_70_y = int(len(y) * 0.7)
        perc_85_y = int(len(y) * 0.85)

        y_train = y[:perc_70_y]
        y_val = y[perc_70_y:perc_85_y]
        y_test = y[perc_85_y:]

        x_scaler, y_scaler = self.__get_scalers(x_train=x_train, y_train=y_train)

        x_train_scaled = x_scaler.transform(x_train)
        x_val_scaled = x_scaler.transform(x_val)
        x_test_scaled = x_scaler.transform(x_test)

        y_train_scaled = y_scaler.transform(y_train)
        y_val_scaled = y_scaler.transform(y_val)
        y_test_scaled = y_scaler.transform(y_test)

        # format data
        SEQ_LENGTH = 12
        x_train_scaled_with_sequences, y_train_scaled_for_sequences = (
            self.__format_data(
                seq_lenght=SEQ_LENGTH,
                x_scaled=x_train_scaled,  # type: ignore
                y_scaled=y_train_scaled,  # type: ignore
            )
        )

        x_val_scaled_with_sequences, y_val_scaled_for_sequences = self.__format_data(
            seq_lenght=SEQ_LENGTH,
            x_scaled=x_val_scaled,  # type: ignore
            y_scaled=y_val_scaled,  # type: ignore
        )

        model = Sequential()
        # model.add(InputLayer(shape=(seq_length, len(self._FEATURES))))
        model.add(LSTM(64, input_shape=(SEQ_LENGTH, len(self._FEATURES))))
        model.add(Dense(8, activation="relu"))
        model.add(Dense(len(self._TARGET), activation="linear"))

        model.compile(
            optimizer="adam",
            loss="mean_squared_error",
            metrics=["root_mean_squared_error"],
        )
        model.fit(
            x=np.array(x_train_scaled_with_sequences),
            y=np.array(y_train_scaled_for_sequences),
            epochs=50,
            validation_data=(x_val_scaled_with_sequences, y_val_scaled_for_sequences),
        )

        x_test_scaled_with_sequences, y_test_scaled_for_sequences = self.__format_data(
            seq_lenght=SEQ_LENGTH,
            x_scaled=x_test_scaled,  # type: ignore
            y_scaled=y_test_scaled,  # type: ignore
        )

        predictions = model.predict(x_test_scaled_with_sequences)

        print(y_test_scaled)
        print(predictions)

        mse = mean_squared_error(y_true=y_test_scaled[:-SEQ_LENGTH], y_pred=predictions)  # type: ignore

        return model, x_scaler, y_scaler, 0.0

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
            await self.past_climate_data_repository.get_past_climate_data(
                location_id=location.id
            )
        )

        start_year, start_month = past_climate_data_df.index[-1]
        start_year = cast(int, start_year)
        start_month = cast(int, start_month)

        # train in thread
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            model, x_scaler, y_scaler, mse = await loop.run_in_executor(
                executor=pool,
                func=lambda: self.__train_model(
                    past_climate_data_df=past_climate_data_df,
                ),
            )

        await self.__save_climate_generative_model(
            location_id=location_id,
            model=model,
            x_scaler=x_scaler,
            y_scaler=y_scaler,
            mse=mse,
        )

    def __generate_climate_data(
        self,
        future_climate_data_df_without_lon_lat: pd.DataFrame,
        seed_past_12_months_data: pd.DataFrame,
        model: Sequential,
    ) -> list[np.ndarray]:
        """Generates future climate data from the latest available past climate data

        Args:
            future_climate_data_df (pd.DataFrame):
            seed_past_12_months_data (pd.DataFrame):
            model (Sequential):

        Returns:
            list[np.ndarray]:
        """
        generated_data: list[np.ndarray] = []
        current_12_months_data = seed_past_12_months_data
        future_climate_data_array = future_climate_data_df_without_lon_lat.to_numpy()
        for _, future_climate_data in enumerate(future_climate_data_array):
            era5_not_in_cmip5_variables_prediction = model.predict(
                np.array([current_12_months_data])
            )[0]

            # contains the next months's data, which is combined  rom prediction and CMIP5 data
            next_month_data_prediction = np.append(
                era5_not_in_cmip5_variables_prediction,
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
            break
        return generated_data

    async def generate_climate_data(
        self,
        location_id: UUID,
    ) -> pd.DataFrame:
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
            await self.past_climate_data_repository.get_past_climate_data_of_previous_12_months(
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
                longitude=location.longitude,
                latitude=location.latitude,
                start_year=start_year,
                start_month=start_month,
            )
        )

        future_climate_data_df = future_climate_data_df[
            (future_climate_data_df.index.get_level_values("year") > start_year)
            | (
                (future_climate_data_df.index.get_level_values("year") == start_year)
                & (future_climate_data_df.index.get_level_values("month") > start_month)
            )
        ]

        future_climate_data_df_without_lon_lat = future_climate_data_df[
            list(copernicus_data_store_api.CMIP5_VARIABLES)
        ]

        data = self.__generate_climate_data(
            future_climate_data_df_without_lon_lat=future_climate_data_df_without_lon_lat,
            seed_past_12_months_data=last_12_months_seed_data,
            model=climate_generative_model.model,
        )

        result = pd.DataFrame(data=data, columns=self._FEATURES)
        result.index = future_climate_data_df.index
        return result

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
            mse=climate_generative_model.mse,
        )

    async def delete_climate_generative_model(self, location_id: UUID):
        async with self.session_maker() as session:
            stmt = delete(ClimateGenerativeModel).where(
                ClimateGenerativeModel.location_id == location_id
            )
            await session.execute(stmt)
            await session.commit()

    async def __save_climate_generative_model(
        self,
        location_id: UUID,
        model: Sequential,
        x_scaler: StandardScaler,
        y_scaler: StandardScaler,
        mse: float,
    ):
        async with self.session_maker() as session:
            stmt = insert(ClimateGenerativeModel).values(
                id=uuid.uuid4(),
                location_id=location_id,
                model=self.__object_to_bytes(model),
                x_scaler=self.__object_to_bytes(x_scaler),
                y_scaler=self.__object_to_bytes(y_scaler),
                mse=mse,
            )
            await session.execute(stmt)
            await session.commit()

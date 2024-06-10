import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast
from uuid import UUID
from io import BytesIO
import uuid
from keras.src.losses import mean_squared_error
import numpy as np
import pandas as pd
from keras.src.models import Sequential
from keras.src.layers import InputLayer, LSTM, Dense
from keras.src.losses import MeanSquaredError
from keras.src.metrics import RootMeanSquaredError
from keras.src.optimizers import Adam
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

BLACKLISTED_TARGET = []


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

    @staticmethod
    def get_cmip5_columns() -> list[str]:
        return [
            "sin_year",
            "cos_year",
            *copernicus_data_store_api.CMIP5_VARIABLES,
        ]

    @staticmethod
    def get_features() -> list[str]:
        return [
            *ClimateGenerativeModelRepository.get_target(),
            *ClimateGenerativeModelRepository.get_cmip5_columns(),
        ]

    @staticmethod
    def get_target() -> list[str]:
        target = copernicus_data_store_api.ERA5_EXCLUSIVE_VARIABLES
        for item in BLACKLISTED_TARGET:
            target.remove(item)
        return target

    @staticmethod
    def get_seq_length() -> int:
        return 12

    @staticmethod
    def __add_sin_cos_year(df: pd.DataFrame):
        # Reset the index to access the multi-index columns
        df_reset = df.reset_index()

        # Convert year and month to a single time representation (fractional year)
        df_reset.drop(columns=["sin_year"], errors="ignore")
        df_reset.drop(columns=["cos_year"], errors="ignore")
        # Create sin and cos features
        df_reset["sin_year"] = np.sin(2 * np.pi * (df_reset["month"] - 1) / 12)
        df_reset["cos_year"] = np.cos(2 * np.pi * (df_reset["month"] - 1) / 12)

        # Optionally, set the index back to the original if needed
        df_reset = df_reset.set_index(["year", "month"])
        return df_reset

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

    @staticmethod
    def __format_data(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x_train_scaled_with_sequences = []
        y_train_scaled_for_model = []
        for i in range(len(x) - ClimateGenerativeModelRepository.get_seq_length()):
            x_train_scaled_with_sequences.append(
                x[i : i + ClimateGenerativeModelRepository.get_seq_length()]
            )
            y_train_scaled_for_model.append(
                y[i + ClimateGenerativeModelRepository.get_seq_length()]
            )

        x_train_scaled_with_sequences = np.array(x_train_scaled_with_sequences)
        y_train_scaled_for_model = np.array(y_train_scaled_for_model)
        return x_train_scaled_with_sequences, y_train_scaled_for_model

    @staticmethod
    def generate_data_from_seed(
        model: Sequential,
        x_scaler: StandardScaler,
        y_scaler: StandardScaler,
        seed_data: np.ndarray,
        future_climate_data_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generates climate data for year, month > seed_data.

        Args:
            model (Sequential):
            x_scaler (StandardScaler):
            y_scaler (StandardScaler):
            seed_data (np.ndarray):
            future_climate_data_df (pd.DataFrame): future data that has to start from the month after seed_data

        Returns:
            pd.DataFrame:
        """
        generated_data = []
        # (SEQ_LENGHT, len(get_features()))
        current_step = seed_data
        year_col: list[int] = []
        month_col: list[int] = []
        for index, row in future_climate_data_df.iterrows():
            year, month = cast(pd.MultiIndex, index)
            year_col.append(year)
            month_col.append(month)
            # (SEQ_LENGHT, len(get_features()))
            scaled_current_step = cast(
                np.ndarray,
                x_scaler.inverse_transform(current_step),
            )

            # (len(get_target()),)
            scaled_prediction = cast(
                np.ndarray, model(np.array([scaled_current_step]))
            )[0]

            # (len(get_target()),)
            prediction = cast(
                np.ndarray, y_scaler.inverse_transform(np.array([scaled_prediction]))
            )[0]

            # (len(get_features()),)
            enriched_prediction = np.concatenate([prediction, row.to_numpy()], axis=0)
            generated_data.append(enriched_prediction)

            current_step = np.concatenate(
                [current_step[1:], np.array([enriched_prediction])]
            )

        result = pd.DataFrame(
            data=generated_data, columns=ClimateGenerativeModelRepository.get_features()
        )
        result["year"] = year_col
        result["month"] = month_col

        result = result.set_index(keys=["year", "month"], drop=True)

        return result

    def __train_model(
        self, past_climate_data_df: pd.DataFrame
    ) -> tuple[Sequential, StandardScaler, StandardScaler, float]:

        past_climate_data_df = ClimateGenerativeModelRepository.__add_sin_cos_year(
            past_climate_data_df
        )
        past_climate_data_df = past_climate_data_df[
            ClimateGenerativeModelRepository.get_features()
        ]

        x_df = past_climate_data_df[ClimateGenerativeModelRepository.get_features()]
        y_df = past_climate_data_df[ClimateGenerativeModelRepository.get_target()]

        perc_70 = int(len(x_df) * 0.7)
        perc_85 = int(len(x_df) * 0.85)

        x_df_train, x_df_val, x_df_test = (
            x_df[:perc_70],
            x_df[perc_70:perc_85],
            x_df[perc_85:],
        )
        y_df_train, y_df_val, y_df_test = (
            y_df[:perc_70],
            y_df[perc_70:perc_85],
            y_df[perc_85:],
        )

        x_scaler = StandardScaler()
        y_scaler = StandardScaler()

        x_scaler = StandardScaler()
        x_scaler = x_scaler.fit(x_df_train)

        y_scaler = StandardScaler()
        y_scaler = y_scaler.fit(y_df_train)

        x_train_scaled, x_val_scaled, x_test_scaled = (
            cast(np.ndarray, x_scaler.transform(x_df_train)),
            cast(np.ndarray, x_scaler.transform(x_df_val)),
            cast(np.ndarray, x_scaler.transform(x_df_test)),
        )
        y_train_scaled, y_val_scaled, y_test_scaled = (
            cast(np.ndarray, y_scaler.transform(y_df_train)),
            cast(np.ndarray, y_scaler.transform(y_df_val)),
            cast(np.ndarray, y_scaler.transform(y_df_test)),
        )

        x_train_formatted, y_train_formatted = (
            ClimateGenerativeModelRepository.__format_data(
                x=x_train_scaled, y=y_train_scaled
            )
        )
        x_val_formatted, y_val_formatted = (
            ClimateGenerativeModelRepository.__format_data(
                x=x_val_scaled, y=y_val_scaled
            )
        )
        x_test_formatted, y_test_formatted = (
            ClimateGenerativeModelRepository.__format_data(
                x=x_test_scaled, y=y_test_scaled
            )
        )

        model = Sequential()
        model.add(
            InputLayer(
                shape=(
                    ClimateGenerativeModelRepository.get_seq_length(),
                    len(ClimateGenerativeModelRepository.get_features()),
                )
            )
        )
        model.add(LSTM(units=64))
        model.add(Dense(units=8))
        model.add(Dense(units=len(ClimateGenerativeModelRepository.get_target())))

        model.compile(loss=MeanSquaredError(), optimizer=Adam(learning_rate=0.0001), metrics=[RootMeanSquaredError()])  # type: ignore

        model.fit(
            x=x_train_formatted,
            y=y_train_formatted,
            validation_data=(x_val_formatted, y_val_formatted),
            epochs=50,
        )

        rmse = model.evaluate(x=x_test_formatted, y=y_test_formatted)[1]

        return model, x_scaler, y_scaler, rmse

    async def create_model_for_location(
        self,
        location_id: UUID,
    ) -> ClimateGenerativeModelDTO:
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
            model, x_scaler, y_scaler, rmse = await loop.run_in_executor(
                executor=pool,
                func=lambda: self.__train_model(
                    past_climate_data_df=past_climate_data_df,
                ),
            )

        id = await self.__save_climate_generative_model(
            location_id=location_id,
            model=model,
            x_scaler=x_scaler,
            y_scaler=y_scaler,
            rmse=rmse,
        )

        return ClimateGenerativeModelDTO(
            id=id,
            location_id=location_id,
            model=model,
            x_scaler=x_scaler,
            y_scaler=y_scaler,
            rmse=rmse
        )

    def generate_climate_data_from_seed(
        self,
        future_climate_data_df: pd.DataFrame,
        seed_data: pd.DataFrame,
        model: Sequential,
    ) -> list[np.ndarray]:
        """Generates future climate data from the latest available past climate data

        Args:
            future_climate_data_df (pd.DataFrame):
            seed_data (pd.DataFrame):
            model (Sequential):

        Returns:
            list[np.ndarray]:
        """
        generated_data: list[np.ndarray] = []
        current_sequences = seed_data
        future_climate_data_array = future_climate_data_df[
            ClimateGenerativeModelRepository.get_features()
        ].to_numpy()
        for _, future_climate_data in enumerate(future_climate_data_array):
            prediction = model.predict(np.array([current_sequences]))[0]

            # contains the next months's data, which is combined  rom prediction and CMIP5 data
            enriched_prediction = np.append(
                prediction,
                future_climate_data,
                axis=0,
            )

            generated_data.append(enriched_prediction)

            # remove the first month of data and push the next month's generated data
            current_sequences = np.append(
                current_sequences[1:],
                [enriched_prediction],
                axis=0,
            )
            break
        return generated_data

    async def generate_climate_data_from_last_past_climate_data(
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

        last_n_months_seed_data = ClimateDataDTO.from_list_to_dataframe(
            await self.past_climate_data_repository.get_past_climate_data_of_previous_n_months(
                location_id=location_id,
                n=ClimateGenerativeModelRepository.get_seq_length(),
            )
        )
        last_n_months_seed_data = last_n_months_seed_data[self.get_features()]

        index = last_n_months_seed_data.index[-1]
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

        data = self.generate_climate_data_from_seed(
            future_climate_data_df=future_climate_data_df,
            seed_data=last_n_months_seed_data,
            model=climate_generative_model.model,
        )

        result = pd.DataFrame(data=data, columns=self.get_features())
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
            rmse=climate_generative_model.mse,
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
        rmse: float,
    ) -> UUID:
        model_id = uuid.uuid4()
        async with self.session_maker() as session:
            stmt = insert(ClimateGenerativeModel).values(
                id=model_id,
                location_id=location_id,
                model=self.__object_to_bytes(model),
                x_scaler=self.__object_to_bytes(x_scaler),
                y_scaler=self.__object_to_bytes(y_scaler),
                mse=rmse,
            )
            await session.execute(stmt)
            await session.commit()
        return model_id

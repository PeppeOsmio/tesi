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

BLACKLISTED_TARGET = [
    "surface_net_solar_radiation",
    "surface_net_thermal_radiation",
    "snowfall",
    "total_cloud_cover",
    "2m_dewpoint_temperature",
]


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
            try:
                target.remove(item)
            except Exception:
                pass
        return target

    @staticmethod
    def get_seq_length() -> int:
        return 12

    @staticmethod
    def add_sin_cos_year(df: pd.DataFrame):
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

    @staticmethod
    def format_data(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
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

    def __train_model(
        self, location_id: UUID, past_climate_data_df: pd.DataFrame
    ) -> ClimateGenerativeModelDTO:
        """_summary_

        Args:
            past_climate_data_df (pd.DataFrame): _description_

        Returns:
            model, x_scaler, y_scaler, rmse, x_train_from
        """
        past_climate_data_df = ClimateGenerativeModelRepository.add_sin_cos_year(
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
        x_scaler = x_scaler.fit(x_df_train.to_numpy())

        y_scaler = StandardScaler()
        y_scaler = y_scaler.fit(y_df_train.to_numpy())

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
            ClimateGenerativeModelRepository.format_data(
                x=x_train_scaled, y=y_train_scaled
            )
        )
        x_val_formatted, y_val_formatted = ClimateGenerativeModelRepository.format_data(
            x=x_val_scaled, y=y_val_scaled
        )
        x_test_formatted, y_test_formatted = (
            ClimateGenerativeModelRepository.format_data(
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

        train_start_year, train_start_month = x_df_train.index[0]
        train_end_year, train_end_month = x_df_train.index[-1]

        validation_start_year, validation_start_month = x_df_val.index[0]
        validation_end_year, validation_end_month = x_df_val.index[-1]

        test_start_year, test_start_month = x_df_test.index[0]
        test_end_year, test_end_month = x_df_test.index[-1]

        return ClimateGenerativeModelDTO(
            id=uuid.uuid4(),
            location_id=location_id,
            model=model,
            x_scaler=x_scaler,
            y_scaler=y_scaler,
            rmse=rmse,
            train_start_year=train_start_year,
            train_start_month=train_start_month,
            train_end_year=train_end_year,
            train_end_month=train_end_month,
            validation_start_year=validation_start_year,
            validation_start_month=validation_start_month,
            validation_end_year=validation_end_year,
            validation_end_month=validation_end_month,
            test_start_year=test_start_year,
            test_start_month=test_start_month,
            test_end_year=test_end_year,
            test_end_month=test_end_month,
        )

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
            climate_generative_model = await loop.run_in_executor(
                executor=pool,
                func=lambda: self.__train_model(
                    location_id=location_id,
                    past_climate_data_df=past_climate_data_df,
                ),
            )

        await self.__save_climate_generative_model(
            climate_generative_model=climate_generative_model
        )

        return climate_generative_model

    def generate_data_from_seed(
        self,
        model: Sequential,
        x_scaler: StandardScaler,
        y_scaler: StandardScaler,
        seed_data: pd.DataFrame,
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
        seed_data = ClimateGenerativeModelRepository.add_sin_cos_year(seed_data)
        seed_data = seed_data[ClimateGenerativeModelRepository.get_features()]
        future_climate_data_df = ClimateGenerativeModelRepository.add_sin_cos_year(
            future_climate_data_df
        )
        future_climate_data_df = future_climate_data_df[
            ClimateGenerativeModelRepository.get_cmip5_columns()
        ]
        generated_data = []
        # (SEQ_LENGHT, len(get_features()))
        current_step = seed_data.to_numpy()
        year_col: list[int] = []
        month_col: list[int] = []
        for index, row in future_climate_data_df.iterrows():
            year, month = cast(pd.MultiIndex, index)
            year_col.append(year)
            month_col.append(month)
            # (SEQ_LENGHT, len(get_features()))
            scaled_current_step = cast(
                np.ndarray,
                x_scaler.transform(current_step),
            )
            
            print(f"current_step.soil_temperature_level_3: {current_step[:, 0]}")

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

            print(f"enriched_prediction.soil_temperature_level_3: {enriched_prediction[0]}")

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

        print(last_n_months_seed_data.tail().index)
        print(future_climate_data_df.head().index)
        

        data = self.generate_data_from_seed(
            model=climate_generative_model.model,
            x_scaler=climate_generative_model.x_scaler,
            y_scaler=climate_generative_model.y_scaler,
            seed_data=last_n_months_seed_data,
            future_climate_data_df=future_climate_data_df,
        )

        result = pd.DataFrame(data=data, columns=self.get_features())
        print(data.shape)
        print(future_climate_data_df.shape)
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
            rmse=climate_generative_model.rmse,
            train_start_year=climate_generative_model.test_start_year,
            train_start_month=climate_generative_model.train_start_month,
            validation_start_year=climate_generative_model.validation_start_year,
            validation_start_month=climate_generative_model.validation_start_month,
            test_start_year=climate_generative_model.test_start_year,
            test_start_month=climate_generative_model.test_start_month,
            train_end_year=climate_generative_model.train_end_year,
            train_end_month=climate_generative_model.train_end_month,
            validation_end_year=climate_generative_model.validation_end_year,
            validation_end_month=climate_generative_model.validation_end_month,
            test_end_year=climate_generative_model.test_end_year,
            test_end_month=climate_generative_model.test_end_month,
        )

    async def delete_climate_generative_model(self, location_id: UUID):
        async with self.session_maker() as session:
            stmt = delete(ClimateGenerativeModel).where(
                ClimateGenerativeModel.location_id == location_id
            )
            await session.execute(stmt)
            await session.commit()

    async def __save_climate_generative_model(
        self, climate_generative_model: ClimateGenerativeModelDTO
    ) -> UUID:
        model_id = uuid.uuid4()
        async with self.session_maker() as session:
            stmt = insert(ClimateGenerativeModel).values(
                id=climate_generative_model.id,
                location_id=climate_generative_model.location_id,
                model=self.__object_to_bytes(climate_generative_model.model),
                x_scaler=self.__object_to_bytes(climate_generative_model.x_scaler),
                y_scaler=self.__object_to_bytes(climate_generative_model.y_scaler),
                rmse=climate_generative_model.rmse,
                train_start_year=climate_generative_model.test_start_year,
                train_start_month=climate_generative_model.train_start_month,
                validation_start_year=climate_generative_model.validation_start_year,
                validation_start_month=climate_generative_model.validation_start_month,
                test_start_year=climate_generative_model.test_start_year,
                test_start_month=climate_generative_model.test_start_month,
                train_end_year=climate_generative_model.train_end_year,
                train_end_month=climate_generative_model.train_end_month,
                validation_end_year=climate_generative_model.validation_end_year,
                validation_end_month=climate_generative_model.validation_end_month,
                test_end_year=climate_generative_model.test_end_year,
                test_end_month=climate_generative_model.test_end_month,
            )
            await session.execute(stmt)
            await session.commit()
        return model_id

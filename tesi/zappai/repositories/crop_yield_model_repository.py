from typing import cast
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from tesi.zappai.exceptions import LocationNotFoundError
from tesi.zappai.repositories.climate_generative_model_repository import (
    FEATURES as CLIMATE_GENERATIVE_MODEL_FEATURES,
)
from tesi.zappai.repositories.crop_repository import CropRepository
from tesi.zappai.repositories.crop_yield_data_repository import CropYieldDataRepository
from tesi.zappai.repositories.dtos import ClimateDataDTO, CropYieldDataDTO
from tesi.zappai.repositories.location_repository import LocationRepository
from tesi.zappai.repositories.past_climate_data_repository import (
    PastClimateDataRepository,
)
from uuid import UUID
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

FEATURES = [
    "sowing_year",
    "sowing_month",
    "harvest_year",
    "harvest_month",
    "surface_solar_radiation_downwards_mean",
    "surface_solar_radiation_downwards_std",
    "surface_solar_radiation_downwards_min",
    "surface_solar_radiation_downwards_max",
    "surface_thermal_radiation_downwards_mean",
    "surface_thermal_radiation_downwards_std",
    "surface_thermal_radiation_downwards_min",
    "surface_thermal_radiation_downwards_max",
    "surface_net_solar_radiation_mean",
    "surface_net_solar_radiation_std",
    "surface_net_solar_radiation_min",
    "surface_net_solar_radiation_max",
    "surface_net_thermal_radiation_mean",
    "surface_net_thermal_radiation_std",
    "surface_net_thermal_radiation_min",
    "surface_net_thermal_radiation_max",
    "total_cloud_cover_mean",
    "total_cloud_cover_std",
    "total_cloud_cover_min",
    "total_cloud_cover_max",
    "2m_dewpoint_temperature_mean",
    "2m_dewpoint_temperature_std",
    "2m_dewpoint_temperature_min",
    "2m_dewpoint_temperature_max",
    "soil_temperature_level_3_mean",
    "soil_temperature_level_3_std",
    "soil_temperature_level_3_min",
    "soil_temperature_level_3_max",
    "volumetric_soil_water_layer_3_mean",
    "volumetric_soil_water_layer_3_std",
    "volumetric_soil_water_layer_3_min",
    "volumetric_soil_water_layer_3_max",
    "2m_temperature_mean",
    "2m_temperature_std",
    "2m_temperature_min",
    "2m_temperature_max",
    "total_precipitation_mean",
    "total_precipitation_std",
    "total_precipitation_min",
    "total_precipitation_max",
]
TARGET = ["_yield"]


class CropYieldModelRepository:
    def __init__(
        self,
        past_climate_data_repository: PastClimateDataRepository,
        location_repository: LocationRepository,
        crop_yield_data_repository: CropYieldDataRepository,
        crop_repository: CropRepository,
    ) -> None:
        self.past_climate_data_repository = past_climate_data_repository
        self.location_repository = location_repository
        self.crop_yield_data_repository = crop_yield_data_repository
        self.crop_repository = crop_repository

    async def train_crop_yield_model(self, crop_id: UUID) -> tuple[
        RandomForestRegressor,
        float,
        float,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
    ]:
        crop_yield_data = await self.crop_yield_data_repository.get_crop_yield_data(
            crop_id=crop_id
        )
        crop_yield_data_df = CropYieldDataDTO.from_list_to_dataframe(crop_yield_data)

        enriched_crop_yield_data_df = pd.DataFrame()

        for _, row in crop_yield_data_df.iterrows():
            location = await self.location_repository.get_location_by_id(
                row["location_id"]
            )
            if location is None:
                raise LocationNotFoundError()
            past_climate_data_df = ClimateDataDTO.from_list_to_dataframe(
                await self.past_climate_data_repository.get_past_climate_data(
                    location_id=location.id,
                    year_from=row["sowing_year"],
                    month_from=row["sowing_month"],
                    year_to=row["harvest_year"],
                    month_to=row["harvest_month"],
                )
            )
            past_climate_data_df = past_climate_data_df[
                CLIMATE_GENERATIVE_MODEL_FEATURES
            ]
            stats = ["mean", "std", "min", "max"]
            climate_data_stats = past_climate_data_df.agg(
                {feature: stats for feature in CLIMATE_GENERATIVE_MODEL_FEATURES},  # type: ignore
                axis=0,
            )  # type: ignore
            result_climate_data_stats_df = pd.DataFrame()
            for feature in CLIMATE_GENERATIVE_MODEL_FEATURES:
                for stat in stats:
                    result_climate_data_stats_df[f"{feature}_{stat}"] = [
                        climate_data_stats.loc[stat][feature]
                    ]
            # convert the row to a DataFrame
            crop_yield_data_row_df = pd.DataFrame([row])
            # since the row was a Series, remove the useless index column that the DataFrame inherited
            crop_yield_data_row_df = crop_yield_data_row_df.drop(columns=["index"])
            crop_yield_data_row_df = crop_yield_data_row_df.reset_index(drop=True)
            enriched_crop_yield_data_row = pd.concat(
                [crop_yield_data_row_df, result_climate_data_stats_df], axis=1
            )
            enriched_crop_yield_data_df = pd.concat(
                [enriched_crop_yield_data_df, enriched_crop_yield_data_row],
                axis=0,
            )

        enriched_crop_yield_data_df = enriched_crop_yield_data_df[[*FEATURES, *TARGET]]
        enriched_crop_yield_data_df = enriched_crop_yield_data_df.reset_index(drop=True)

        x = enriched_crop_yield_data_df[FEATURES]
        y = enriched_crop_yield_data_df[TARGET]
        x_train, x_test, y_train, y_test = cast(
            tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
            train_test_split(x, y, test_size=0.2, train_size=0.8, random_state=42),
        )

        model = RandomForestRegressor(
            n_estimators=100,
            criterion="squared_error",
            min_samples_split=50,
            random_state=42,
        )
        model.fit(x_train.to_numpy(), y_train.to_numpy().flatten())

        y_pred = model.predict(x_test.to_numpy())
        mse = cast(float, mean_squared_error(y_true=y_test, y_pred=y_pred))
        r2 = cast(float, r2_score(y_true=y_test, y_pred=y_pred))

        return model, mse, r2, x_train, x_test, y_train, y_test

    async def save_crop_yield_model_for_all_crops(self):
        crops = await self.crop_repository.get_all_crops()

        processed = 0

        def print_processed():
            print(f"\rCrop yield models saved: {processed}/{len(crops)}", end="")

        print_processed()
        for crop in crops:
            model, mse, r2, _, _, _, _ = await self.train_crop_yield_model(
                crop_id=crop.id
            )
            await self.crop_repository.save_crop_yield_model(
                crop_id=crop.id, crop_yield_model=model, mse=mse, r2=r2
            )
            processed += 1
            print_processed()

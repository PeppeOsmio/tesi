from dataclasses import dataclass
from typing import cast
from uuid import UUID

import pandas as pd
from tesi.zappai.exceptions import LocationNotFoundError
from tesi.zappai.repositories.climate_generative_model_repository import (
    ClimateGenerativeModelRepository,
)
from tesi.zappai.repositories.crop_repository import CropRepository
from tesi.zappai.dtos import ClimateDataDTO, CropDTO, FutureClimateDataDTO
from tesi.zappai.repositories.future_climate_data_repository import (
    FutureClimateDataRepository,
)
from tesi.zappai.repositories.location_repository import LocationRepository
from tesi.zappai.repositories.past_climate_data_repository import (
    PastClimateDataRepository,
)
from tesi.zappai.utils.common import (
    calc_months_delta,
    enrich_data_frame_with_stats,
    get_next_n_months,
)
from tesi.zappai.utils.genetic import (
    GeneticAlgorithm,
    Individual,
    Population,
    individual_to_int,
)
from sklearn.ensemble import RandomForestRegressor
from tesi.zappai.services.crop_yield_model_service import (
    FEATURES as CROP_YIELD_MODEL_FEATURES,
    TARGET as CROP_YIELD_MODEL_TARGET,
)


@dataclass
class SowingAndHarvestingDTO:
    sowing_year: int
    sowing_month: int
    harvest_year: int
    harvest_month: int
    estimated_yield_per_hectar: float
    duration: int


@dataclass
class CropOptimizerResultDTO:
    best_combinations: list[SowingAndHarvestingDTO]
    forecast: list[ClimateDataDTO]


class CropOptimizerService:
    def __init__(
        self,
        crop_repository: CropRepository,
        past_climate_data_repository: PastClimateDataRepository,
        future_climate_data_repository: FutureClimateDataRepository,
        location_repository: LocationRepository,
        climate_generative_model_repository: ClimateGenerativeModelRepository,
    ) -> None:
        self.crop_repository = crop_repository
        self.past_climate_data_repository = past_climate_data_repository
        self.future_climate_data_repository = future_climate_data_repository
        self.location_repository = location_repository
        self.climate_generative_model_repository = climate_generative_model_repository

    async def get_best_crop_sowing_and_harvesting(
        self, crop_id: UUID, location_id: UUID
    ) -> CropOptimizerResultDTO:
        """_summary_

        Args:
            crop_id (UUID): _description_
            location_id (UUID): _description_
            start_year (int): _description_
            start_month (int): _description_

        Returns:
            CropOptimizerResultDTO:
        """
        location = await self.location_repository.get_location_by_id(location_id)

        if location is None:
            raise Exception()

        crop = await self.crop_repository.get_crop_by_id(crop_id)
        if crop is None:
            raise Exception()

        model = crop.crop_yield_model
        if model is None:
            raise Exception()

        forecast = await self.climate_generative_model_repository.generate_climate_data_from_last_past_climate_data(
            location_id=location.id, months=24
        )
        forecast_df = ClimateDataDTO.from_list_to_dataframe(forecast)
        forecast_df = forecast_df.drop(columns=["location_id"])

        POPULATIONS = 20

        def fitness_func(individual: Individual) -> float:
            if len(individual) != 10:
                raise Exception(f"Bro individual must be of size 10...")
            sowing = individual_to_int(individual[:5])
            harvesting = individual_to_int(individual[5:])

            if (sowing >= len(forecast)) | (harvesting >= len(forecast)):
                return 0

            sowing_year, sowing_month = forecast_df.index[sowing]
            harvest_year, harvest_month = forecast_df.index[harvesting]

            duration = calc_months_delta(
                start_year=sowing_year,
                start_month=sowing_month,
                end_year=harvest_year,
                end_month=harvest_month,
            )

            if duration <= 0:
                return 0
            if (duration < cast(int, cast(CropDTO, crop).min_farming_months)) | (
                duration > cast(int, cast(CropDTO, crop).max_farming_months)
            ):
                return 0

            forecast_for_individual = forecast_df[
                (
                    (forecast_df.index.get_level_values("year") < harvest_year)
                    | (
                        (forecast_df.index.get_level_values("year") == harvest_year)
                        & (forecast_df.index.get_level_values("year") <= harvest_month)
                    )
                )
                | (
                    (forecast_df.index.get_level_values("year") > sowing_year)
                    | (
                        (forecast_df.index.get_level_values("year") == sowing_year)
                        & (forecast_df.index.get_level_values("year") >= sowing_month)
                    )
                )
            ]

            enriched_forecast = enrich_data_frame_with_stats(df=forecast_for_individual, ignore=[])

            x_df = pd.DataFrame(
                {
                    "sowing_year": [sowing_year],
                    "sowing_month": [sowing_month],
                    "harvest_year": [harvest_year],
                    "harvest_month": [harvest_month],
                    "duration_months": calc_months_delta(
                        start_year=sowing_year,
                        start_month=sowing_month,
                        end_year=harvest_year,
                        end_month=harvest_month,
                    ),
                }
            )
            x_df = pd.concat([x_df, enriched_forecast], axis=1)

            pred = cast(RandomForestRegressor, model).predict(
                x_df[CROP_YIELD_MODEL_FEATURES].to_numpy()
            )
            return pred[0]

        def on_population_created(i: int, population: Population):
            return
            print(f"\rPOPULATION {i}/{POPULATIONS} PROCESSED!!!", end="")
            if i == POPULATIONS:
                print()

        ga = GeneticAlgorithm(
            fitness=fitness_func,
            chromosome_length=10,
            population_size=POPULATIONS,
            mutation_rate=0.01,
            crossover_rate=0.7,
            generations=20,
            on_population_created=on_population_created,
        )

        combinations: list[SowingAndHarvestingDTO] = []

        results, fitnesses = ga.run()

        for i in range(len(results)):
            result = results[i]
            fitness = fitnesses[i]

            sowing = individual_to_int(result[:5])
            harvesting = individual_to_int(result[5:])

            sowing_year, sowing_month = forecast_df.index[sowing]
            harvest_year, harvest_month = forecast_df.index[harvesting]
            duration = calc_months_delta(
                start_year=sowing_year,
                start_month=sowing_month,
                end_year=harvest_year,
                end_month=harvest_month,
            )
            combinations.append(
                SowingAndHarvestingDTO(
                    sowing_year=sowing_year,
                    sowing_month=sowing_month,
                    harvest_year=harvest_year,
                    harvest_month=harvest_month,
                    estimated_yield_per_hectar=fitness,
                    duration=duration,
                )
            )
        return CropOptimizerResultDTO(
            best_combinations=combinations,
            forecast=forecast,
        )

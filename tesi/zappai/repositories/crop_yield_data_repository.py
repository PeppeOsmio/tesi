import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from io import StringIO
import logging
import os
from typing import Any, cast
import uuid
import pandas as pd
import requests
from sqlalchemy import delete, insert, select
from tesi.zappai.repositories.dtos import CropDTO, LocationClimateYearsDTO
from tesi.zappai.models import Crop, CropYieldData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tesi.zappai.repositories.crop_repository import CropRepository
from tesi.zappai.repositories.location_repository import LocationRepository

all_columns = [
    "Author",
    "Journal",
    "Year",
    "Site country",
    "Location",
    "Latitude",
    "Longitude",
    "Soil information recorded in the paper",
    "pH (surface layer)",
    "Replications in experiment",
    "Crop",
    "Initial year of NT practice ( or first year of experiment if missing)",
    "Sowing year",
    "Harvest year",
    "Years since NT started (yrs)",
    "Crop growing season recorded in the paper",
    "Crop rotation with at least 3 crops involved in CT",
    "Crop rotation with at least 3 crops involved in NT",
    "Crop sequence (details)",
    "Cover crop before sowing",
    "Soil cover in CT",
    "Soil cover in NT",
    "Residue management of previous crop in CT  (details)",
    "Residue management of previous crop in NT (details)",
    "Weed and pest control CT",
    "Weed and pest control NT ",
    "Weed and pest control CT (details)",
    "Weed and pest control NT  (details)",
    "Fertilization CT ",
    "Fertilization NT",
    "N input",
    "N input rates with the unit kg N ha-1 (details)",
    "Field fertilization (details)",
    "Irrigation CT",
    "Irrigation NT",
    "Water applied in CT",
    "Water applied in NT",
    "Other information",
    "Yield of CT",
    "Yield of NT",
    "Relative yield change",
    "Yield increase with NT",
    "Outlier of CT",
    "Outlier of NT",
    "Sowing month",
    "Harvesting month",
    "P",
    "E",
    "PB",
    "Tave",
    "Tmax",
    "Tmin",
    "ST",
]


columns_to_include: dict[str, str] = {
    "Site country": "country",
    "Location": "location",
    "Latitude": "latitude",
    "Longitude": "longitude",
    # "Soil information recorded in the paper": "soil",
    # "pH (surface layer)": "ph",
    "Crop": "crop",
    "Sowing year": "sowing_year",
    "Sowing month": "sowing_month",
    "Harvest year": "harvest_year",
    "Harvesting month": "harvest_month",
    # "Yield of CT": "yield_ct",
    "Yield of NT": "yield",
    # "P": "P",
    # "E": "E",
    # "PB": "PB",
    # "Tave": "Tave",
    # "Tmax": "Tmax",
    # "Tmin": "Tmin",
    # "ST": "ST",
}


class CropYieldDataRepository:
    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        crop_repository: CropRepository,
        location_repository: LocationRepository,
    ) -> None:
        self.session_maker = session_maker
        self.crop_repository = crop_repository
        self.location_repository = location_repository

    def __download_crops_yield_data(self) -> pd.DataFrame:
        url = "https://figshare.com/ndownloader/files/26690678"

        logging.info(f"Downloading crop yield data from {url}")

        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(
                f"Can't fetch crop database from {url}. Status {response.status_code}, details {response.text}"
            )

        df = pd.read_csv(
            StringIO(initial_value=response.text),
            usecols=list(columns_to_include.keys()),
        )
        df = df.filter(items=list(columns_to_include.keys())).rename(
            columns=columns_to_include
        )

        df = df.dropna(
            subset=[
                "longitude",
                "latitude",
                "crop",
                "yield",
                "sowing_month",
                "harvest_month",
                "sowing_year",
                "harvest_year",
            ],
        )

        df["crop"] = df["crop"].str.replace(r"\.autumn$", "", regex=True)
        df["crop"] = df["crop"].str.replace(r"\.winter$", "", regex=True)
        df["crop"] = df["crop"].str.replace(r"\.spring$", "", regex=True)
        df["crop"] = df["crop"].str.replace(r"\.summer$", "", regex=True)

        df.sort_values(by=["crop", "country", "location"], ascending=[True, True, True])

        df = df.reset_index(drop=True)
        return df

    async def download_crop_yield_data(self):
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            crop_yield_data_df = await loop.run_in_executor(
                executor=pool, func=self.__download_crops_yield_data
            )

        async with self.session_maker() as session:

            logging.info("Checking crops to create")
            crop_names_to_ids: dict[str, uuid.UUID] = {}

            crop_names = set(cast(list[str], list(crop_yield_data_df["crop"])))
            for crop_name in crop_names:
                crop = await self.crop_repository.get_crop_by_name(crop_name)
                if crop is not None:
                    crop_names_to_ids.update({crop_name: crop.id})
                    continue
                logging.info(f"Creating crop {crop_name}")
                crop = await self.crop_repository.create_crop(crop_name)
                crop_names_to_ids.update({crop_name: crop.id})

            logging.info("Checking locations to create")
            location_coordinates_to_ids: dict[str, uuid.UUID] = {}

            locations_df = crop_yield_data_df[
                ["country", "location", "latitude", "longitude"]
            ].drop_duplicates()
            locations_tuples = cast(
                list[tuple[str, str, float, float]],
                list(locations_df.itertuples(index=False, name=None)),
            )
            for country, location_name, latitude, longitude in locations_tuples:
                location = await self.location_repository.get_location_by_coordinates(
                    longitude=longitude, latitude=latitude
                )
                if location is not None:
                    location_coordinates_to_ids.update(
                        {str((longitude, latitude)): location.id}
                    )
                    continue
                logging.info(
                    f"Creating location {location_name} at {longitude} {latitude}"
                )
                location = await self.location_repository.create_location(
                    country=country,
                    name=location_name,
                    longitude=longitude,
                    latitude=latitude,
                )
                location_coordinates_to_ids.update(
                    {str((longitude, latitude)): location.id}
                )

            await session.execute(delete(CropYieldData))

            logging.info("Starting creating crop yield data")
            processed = 0
            STEP = 1000
            logging.info(f"{processed}/{len(crop_yield_data_df)}")
            while processed < len(crop_yield_data_df):
                rows = crop_yield_data_df[processed : processed + STEP]
                values_dicts: list[dict[str, Any]] = []
                for index, row in rows.iterrows():
                    values_dicts.append(
                        {
                            "id": uuid.uuid4(),
                            "location_id": location_coordinates_to_ids[
                                str((row["longitude"], row["latitude"]))
                            ],
                            "crop_id": crop_names_to_ids[row["crop"]],
                            "sowing_year": row["sowing_year"],
                            "sowing_month": row["sowing_month"],
                            "harvest_year": row["harvest_year"],
                            "harvest_month": row["harvest_month"],
                            "_yield": row["yield"],
                        }
                    )
                await session.execute(insert(CropYieldData), values_dicts)
                processed += len(rows)
                logging.info(f"{processed}/{len(crop_yield_data_df)}")
            await session.commit()

    async def get_crop_by_name(self, name: str) -> CropDTO | None:
        async with self.session_maker() as session:
            stmt = select(Crop).where(Crop.name == name)
            crop = await session.scalar(stmt)
        if crop is None:
            return None
        return self.__crop_model_to_dto(crop)

    async def get_unique_location_climate_years(
        self,
    ) -> list[LocationClimateYearsDTO]:
        async with self.session_maker() as session:
            stmt = (
                select(
                    CropYieldData.location_id,
                    CropYieldData.sowing_year,
                    CropYieldData.harvest_year,
                )
                .order_by(
                    CropYieldData.location_id,
                    CropYieldData.sowing_year,
                    CropYieldData.harvest_year,
                )
                .distinct()
            )
            results = list(await session.execute(stmt))

        location_id_to_years_dict: dict[uuid.UUID, set[int]] = {}
        for result in results:
            location_id, sowing_year, harvest_year = result.tuple()
            if location_id_to_years_dict.get(location_id) is None:
                location_id_to_years_dict.update({location_id: set()})
            location_id_to_years_dict[location_id].add(sowing_year)
            location_id_to_years_dict[location_id].add(harvest_year)

        return [
            LocationClimateYearsDTO(location_id=location_id, years=years)
            for location_id, years in location_id_to_years_dict.items()
        ]

    def __crop_model_to_dto(self, crop: Crop) -> CropDTO:
        return CropDTO(id=crop.id, name=crop.name, created_at=crop.created_at)

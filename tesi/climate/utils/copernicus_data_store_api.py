from datetime import datetime, timezone
import logging
import os
import random
from typing import cast
import cdsapi
import zipfile

import pandas as pd
from tesi.climate.utils import common
from uuid import UUID

FUTURE_DATA_RESPONSE_COLUMNS_MAPPING = {"lon": "longitude", "lat": "latitude"}

PAST_DATA_QUERY_COLUMNS = [
    "soil_temperature_level_1",
    "total_precipitation",
    "surface_net_solar_radiation",
    "surface_pressure",
    "volumetric_soil_water_layer_1",
]


ERA5_ONLY_PARAMETERS = [
    "surface_latent_heat_flux",  # Surface latent heat flux (related to evaporation and transpiration)
    "surface_sensible_heat_flux",  # Surface sensible heat flux
    "soil_temperature_level_1",  # Soil temperature at the first level
    "volumetric_soil_water_layer_1",  # Soil moisture content at the first level
]

ERA5_AND_CMIP5_PARAMETERS = [
    "2m_temperature",  # Temperature at 2 meters
    "total_precipitation",  # Total precipitation
    "mean_sea_level_pressure",  # Mean sea level pressure
    "surface_net_solar_radiation",  # Net solar radiation at the surface
    "surface_pressure",  # Surface pressure
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
]

ERA5_PARAMETERS = [*ERA5_ONLY_PARAMETERS, *ERA5_AND_CMIP5_PARAMETERS]

ERA5_PARAMETERS_MAPPINGS = {
    "t2m": "2m_temperature",  # Temperature at 2 meters
    "tp": "total_precipitation",  # Total precipitation
    "msl": "mean_sea_level_pressure",  # Mean sea level pressure
    "ssr": "surface_net_solar_radiation",  # Net solar radiation at the surface
    "sp": "surface_pressure",
    "u10": "10m_u_component_of_wind",
    "v10": "10m_v_component_of_wind",
    "slhf": "surface_latent_heat_flux",  # Surface latent heat flux (related to evaporation and transpiration)
    "sshf": "surface_sensible_heat_flux",  # Surface sensible heat flux
    "stl1": "soil_temperature_level_1",  # Soil temperature at the first level
    "swvl1": "volumetric_soil_water_layer_1",  # Soil moisture content at the first level
}

CMIP5_PARAMETERS_MAPPINGS = {
    "tas": "2m_temperature",  # Temperature at 2 meters
    "pr": "total_precipitation",  # Total precipitation
    "psl": "mean_sea_level_pressure",  # Mean sea level pressure
    "rsds": "surface_net_solar_radiation",  # Net solar radiation at the surface
    "ps": "surface_pressure",  # Surface pressure
    "uas": "10m_u_component_of_wind",
    "vas": "10m_v_component_of_wind",
}


class CopernicusDataStoreAPI:
    def __init__(self, user_id: int, api_token: UUID) -> None:
        self.cds_client = cdsapi.Client(
            url="https://cds.climate.copernicus.eu/api/v2",
            key=f"{user_id}:{api_token}",
            verify=1,
        )

    def download_future_climate_data(self) -> pd.DataFrame:
        """https://cds.climate.copernicus.eu/cdsapp#!/dataset/sis-hydrology-meteorology-derived-projections?tab=form

        Returns:
            pd.DataFrame: _description_
        """
        dest_dir = "tmp_future_climate"

        os.makedirs(dest_dir, exist_ok=True)

        zip_file = os.path.join(dest_dir, f"{random.randbytes(16).hex()}.zip")

        self.cds_client.retrieve(
            "sis-hydrology-meteorology-derived-projections",
            {
                "format": "zip",
                "period": "2011_2040",
                "ensemble_member": "r12i1p1",
                "gcm": "ec_earth",
                "rcm": "cclm4_8_17",
                "experiment": "rcp_2_6",
                "horizontal_resolution": "5_km",
                "time_aggregation": "monthly_mean",
                "variable_type": "absolute_values",
                "processing_type": "bias_corrected",
                "variable": [
                    "2m_air_temperature",
                    "precipitation",
                ],
                "product_type": "climate_impact_indicators",
            },
            zip_file,
        )

        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(dest_dir)

        os.remove(zip_file)

        precipitations_df = pd.DataFrame()
        temperature_at_surface_df = pd.DataFrame()

        for extracted_file in os.listdir(dest_dir):
            extracted_file_path = os.path.join(dest_dir, extracted_file)
            if not extracted_file.endswith(".nc"):
                continue
            if extracted_file.startswith("prAdjust"):
                precipitations_df = common.convert_nc_file_to_dataframe(
                    source_file_path=extracted_file_path, limit=None
                )
                precipitations_df.rename(
                    columns={"prAdjust_ymonmean": "total_precipitations"}, inplace=True
                )
            elif extracted_file.startswith("tasAdjust"):
                temperature_at_surface_df = common.convert_nc_file_to_dataframe(
                    source_file_path=extracted_file_path, limit=None
                )
                temperature_at_surface_df.rename(
                    columns={"tasAdjust_ymonmean": "surface_temperature"}, inplace=True
                )
            os.remove(extracted_file_path)

        result_df = temperature_at_surface_df
        result_df["total_precipitations"] = precipitations_df["total_precipitations"]
        result_df.drop(columns=["x", "y", "height"], inplace=True)

        result_df = common.process_copernicus_climate_data(
            df=result_df, columns_mappings=FUTURE_DATA_RESPONSE_COLUMNS_MAPPING
        )
        return result_df

    def get_climate_data_of_last_12_months(
        self, longitude: float, latitude: float
    ) -> pd.DataFrame:
        now = datetime.now(tz=timezone.utc)
        current_month = now.month
        current_year = now.year
        c = cdsapi.Client(
            url="https://cds.climate.copernicus.eu/api/v2",
            key="311032:15a4dd58-d44c-4d52-afa3-db18f38e1d2c",
            verify=1,
        )
        tmp_file_path = f"{random.randbytes(32).hex()}.nc"

        c.retrieve(
            "reanalysis-era5-single-levels-monthly-means",
            {
                "format": "netcdf",
                "product_type": "monthly_averaged_reanalysis",
                "variable": PAST_DATA_QUERY_COLUMNS,
                "year": [str(current_year - 1), str(current_year)],
                "month": [str(month).zfill(2) for month in range(1, 13)],
                "time": "00:00",
                "area": [
                    latitude + 0.01,
                    longitude - 0.01,
                    latitude - 0.01,
                    longitude + 0.01,
                ],
            },
            tmp_file_path,
        )
        df = common.convert_nc_file_to_dataframe(
            source_file_path=tmp_file_path, limit=None
        )
        os.remove(tmp_file_path)
        df = common.process_copernicus_climate_data(
            df=df, columns_mappings=PAST_DATA_RESPONSE_COLUMNS_MAPPING
        )

        months_of_last_year_to_remove = range(1, current_month - 1)

        for month in months_of_last_year_to_remove:
            df.drop((current_year - 1, month), inplace=True)

        return df

    def get_past_climate_data_since_1940(
        self, longitude: float, latitude: float
    ) -> pd.DataFrame:

        result_df = pd.DataFrame()

        tmp_dir = "./tmp_global_climate_data"
        os.makedirs(tmp_dir, exist_ok=True)

        STEP = 10
        end = datetime.now(tz=timezone.utc).year
        start = end

        while start >= 1940:
            previous_start = start
            start -= STEP
            actual_start = max(1940, start)

            logging.info(f"Getting data from {actual_start} to {previous_start}")
            tmp_file_path = os.path.join(tmp_dir, f"{random.randbytes(32).hex()}.nc")
            self.cds_client.retrieve(
                name="reanalysis-era5-single-levels-monthly-means",
                request={
                    "product_type": "monthly_averaged_reanalysis",
                    "variable": PAST_DATA_QUERY_COLUMNS,
                    "year": [
                        str(year) for year in range(actual_start, previous_start + 1)
                    ],
                    "month": [str(month).zfill(2) for month in range(1, 13)],
                    "day": [str(day).zfill(2) for day in range(1, 32)],
                    "time": [f"{hour:02d}:00" for hour in range(24)],
                    "format": "netcdf",
                    "area": [
                        latitude + 0.01,
                        longitude - 0.01,
                        latitude - 0.01,
                        longitude + 0.01,
                    ],
                },
                target=tmp_file_path,
            )

            tmp_df = common.convert_nc_file_to_dataframe(
                source_file_path=tmp_file_path, limit=None
            )
            os.remove(tmp_file_path)
            result_df = pd.concat([result_df, tmp_df], axis=0)

        if os.path.exists(tmp_dir):
            os.removedirs(tmp_dir)

        result_df = common.process_copernicus_climate_data(
            df=result_df, columns_mappings=PAST_DATA_RESPONSE_COLUMNS_MAPPING
        )
        result_df["surface_temperature"] = result_df["surface_temperature"] - 273.15
        return result_df


if __name__ == "__main__":
    cds_api = CopernicusDataStoreAPI(
        user_id=311032, api_token=UUID(hex="15a4dd58-d44c-4d52-afa3-db18f38e1d2c")
    )

    df = cds_api.download_future_climate_data()
    df[:100].to_csv("data/future_climate_example.csv")
    os.makedirs("training_data", exist_ok=True)
    df.to_csv("training_data/future_climate.csv")

    result_df = cds_api.get_past_climate_data_since_1940(40.484638, 17.225732)
    result_df[:100].to_csv("data/past_climate_data_example.csv")
    os.makedirs("training_data", exist_ok=True)
    result_df.to_csv("training_data/past_climate_data.csv")
    result_df = cds_api.get_climate_data_of_last_12_months(40.484638, 17.225732)
    result_df.to_csv("data/climate_data_last_12_months_example.csv")

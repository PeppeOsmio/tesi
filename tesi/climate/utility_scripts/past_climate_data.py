from datetime import datetime, timezone
import logging
import os
import random
import cdsapi

import pandas as pd

from tesi.climate.utility_scripts.common import (
    convert_nc_file_to_dataframe,
    process_copernicus_climate_data,
)


QUERY_COLUMNS = [
    "soil_temperature_level_1",
    "total_precipitation",
    "surface_net_solar_radiation",
    "surface_pressure",
    "volumetric_soil_water_layer_1",
]


RESPONSE_COLUMNS_MAPPING = {
    "time": "time",
    "stl1": "surface_temperature",
    "tp": "total_precipitations",
    "ssr": "surface_net_solar_radiation",
    "sp": "surface_pressure",
    "swvl1": "volumetric_soil_water_layer_1",
}


class CopernicusDataStoreAPI:
    def __init__(self, copernicus_data_store_client: cdsapi.Client) -> None:
        self.copernicus_data_store_client = copernicus_data_store_client

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
                "variable": QUERY_COLUMNS,
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
        df = convert_nc_file_to_dataframe(source_file_path=tmp_file_path, limit=None)
        os.remove(tmp_file_path)
        df = process_copernicus_climate_data(
            df=df, columns_mappings=RESPONSE_COLUMNS_MAPPING
        )

        months_of_last_year_to_remove = range(1, current_month - 1)

        for month in months_of_last_year_to_remove:
            df.drop((current_year - 1, month), inplace=True)

        return df

    def get_global_climate_data_since_1940(lat: float, lon: float) -> pd.DataFrame:
        c = cdsapi.Client(
            url="https://cds.climate.copernicus.eu/api/v2",
            key="311032:15a4dd58-d44c-4d52-afa3-db18f38e1d2c",
            verify=1,
        )

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
            c.retrieve(
                name="reanalysis-era5-single-levels-monthly-means",
                request={
                    "product_type": "monthly_averaged_reanalysis",
                    "variable": QUERY_COLUMNS,
                    "year": [
                        str(year) for year in range(actual_start, previous_start + 1)
                    ],
                    "month": [str(month).zfill(2) for month in range(1, 13)],
                    "day": [str(day).zfill(2) for day in range(1, 32)],
                    "time": [f"{hour:02d}:00" for hour in range(24)],
                    "format": "netcdf",
                    "area": [lat + 0.01, lon - 0.01, lat - 0.01, lon + 0.01],
                },
                target=tmp_file_path,
            )

            tmp_df = convert_nc_file_to_dataframe(
                source_file_path=tmp_file_path, limit=None
            )
            os.remove(tmp_file_path)
            result_df = pd.concat([result_df, tmp_df], axis=0)

        if os.path.exists(tmp_dir):
            os.removedirs(tmp_dir)

        result_df = process_copernicus_climate_data(
            df=result_df, columns_mappings=RESPONSE_COLUMNS_MAPPING
        )
        result_df["surface_temperature"] = result_df["surface_temperature"] - 273.15
        return result_df


def main():
    result_df = get_global_climate_data_since_1940(40.484638, 17.225732)
    result_df[:100].to_csv("data/past_climate_data_example.csv")
    os.makedirs("training_data", exist_ok=True)
    result_df.to_csv("training_data/past_climate_data.csv")
    result_df = get_climate_data_of_last_12_months(40.484638, 17.225732)
    result_df.to_csv("data/climate_data_last_12_months_example.csv")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

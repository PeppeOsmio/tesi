from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from enum import StrEnum
import logging
import os
import random
import cdsapi
import asyncio

import pandas as pd
import xarray as xr
from typing import cast


QUERY_COLUMNS = [
    "2m_temperature",
    "total_precipitation",
    "10m_wind_speed",
    "precipitation_type",
    "surface_net_solar_radiation",
    "snow_depth",
    "surface_pressure",
    "volumetric_soil_water_layer_1"
]


RESPONSE_COLUMNS_MAPPING = {
    "time": "time",
    "t2m": "2m_temperature",
    "tp": "total_precipitation",
    "si10": "10m_wind_speed",
    "ptype": "precipitation_type",
    "sd": "snow_depth",
    "ssr":"surface_net_solar_radiation",
    "sp": "surface_pressure",
    "swvl1": "volumetric_soil_water_layer_1",
}


def get_climate_data_since_1940_sync(lat: float, lon: float):
    """
    Download ERA5 reanalysis data for a specific latitude and longitude from Copernicus Climate Data Store, aggregated by month from 1940 to last month.
    https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels-monthly-means?tab=form

    :param lat: Latitude
    :param lon: Longitude
    :param start_year: Start year
    :param end_year: End year
    :return: File path to the downloaded data
    """
    c = cdsapi.Client(
        url="https://cds.climate.copernicus.eu/api/v2",
        key="311032:15a4dd58-d44c-4d52-afa3-db18f38e1d2c",
        verify=1,
    )

    end_year = datetime.now(tz=timezone.utc).year
    if end_year < 1940:
        raise ValueError(
            f"The current year ({end_year}) must be at least 1940! Did you travel back in time?"
        )
    df = pd.DataFrame()

    start_year = end_year
    STEP_YEARS = 10

    while start_year >= 1940:
        old_start_year = start_year
        start_year -= STEP_YEARS
        tmp_file_path = f"{random.randbytes(32).hex()}.nc"

        actual_start_year = max(1940, start_year)
        logging.info(f"Getting data from {actual_start_year} to {old_start_year}")
        c.retrieve(
            name="reanalysis-era5-single-levels-monthly-means",
            request={
                "product_type": "monthly_averaged_reanalysis",
                "variable": QUERY_COLUMNS,
                "year": [
                    str(year) for year in range(actual_start_year, old_start_year + 1)
                ],
                "month": [str(month).zfill(2) for month in range(1, 13)],
                "day": [str(day).zfill(2) for day in range(1, 32)],
                "time": [f"{hour:02d}:00" for hour in range(24)],
                "area": [lat + 0.01, lon - 0.01, lat - 0.01, lon + 0.01],
                "format": "netcdf",
            },
            target=tmp_file_path,
        )

        # Load the data into an xarray Dataset directly from the binary stream
        ds = xr.open_dataset(tmp_file_path)
        os.remove(tmp_file_path)
        tmp_df = ds.to_dataframe().reset_index()

        print(tmp_df)

        # remove coordinates
        tmp_df.pop("longitude")
        tmp_df.pop("latitude")
        # set time as index
        tmp_df["time"] = pd.to_datetime(tmp_df["time"])
        tmp_df.set_index("time", inplace=True)
        tmp_df.sort_index()

        if "expver" in tmp_df.columns:
            # merge expver 5 into empty expver 1
            df_expver1 = tmp_df[tmp_df["expver"] == 1].drop(columns=["expver"])
            df_expver5 = tmp_df[tmp_df["expver"] == 5].drop(columns=["expver"])

            tmp_df_combined = df_expver1.combine_first(df_expver5)

            tmp_df = tmp_df_combined

        tmp_df = tmp_df.rename(columns=RESPONSE_COLUMNS_MAPPING)
        df = pd.concat([df, tmp_df], axis=0)

    df.sort_index(inplace=True)

    columns = [*df.columns]
    columns = ["year", "month", *columns]
    df["year"] = cast(pd.DatetimeIndex, df.index).year
    df["month"] = cast(pd.DatetimeIndex, df.index).month
    df = df[columns]
    return df


async def get_climate_data_since_1940(lat: float, lon: float) -> pd.DataFrame:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        df = await loop.run_in_executor(
            pool, get_climate_data_since_1940_sync, lat, lon
        )
    return df


async def main():
    # Example usage
    lat, lon = 40.211392, 16.682612  # Policoro

    df = await get_climate_data_since_1940(lat, lon)
    df.to_csv("data/copernicus.csv")


if __name__ == "__main__":
    asyncio.run(main())

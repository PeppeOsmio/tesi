from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import logging
import os
import random
import cdsapi
import asyncio

import pandas as pd
import xarray as xr
from typing import cast

from tesi.utility_scripts.nc_to_csv import convert_nc_file_to_dataframe


QUERY_COLUMNS = [
    "soil_temperature_level_1",
    "total_precipitation",
    # "10m_wind_speed",
    # "precipitation_type",
    # "surface_net_solar_radiation",
    # "snow_depth",
    # "surface_pressure",
    # "volumetric_soil_water_layer_1",
]


RESPONSE_COLUMNS_MAPPING = {
    "time": "time",
    "stl1": "surface_temperature",
    "tp": "total_precipitations",
    # "si10": "10m_wind_speed",
    # "ptype": "precipitation_type",
    # "sd": "snow_depth",
    # "ssr": "surface_net_solar_radiation",
    # "sp": "surface_pressure",
    # "swvl1": "volumetric_soil_water_layer_1",
}


def get_climate_data_of_year(lat: float, lon: float, year: int) -> pd.DataFrame:
    """
    Download ERA5 reanalysis data for a specific latitude and longitude from Copernicus Climate Data Store, aggregated by month.
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

    tmp_file_path = f"{random.randbytes(32).hex()}.nc"

    c.retrieve(
        name="reanalysis-era5-single-levels-monthly-means",
        request={
            "product_type": "monthly_averaged_reanalysis",
            "variable": QUERY_COLUMNS,
            "year": [str(year)],
            "month": [str(month).zfill(2) for month in range(1, 13)],
            "day": [str(day).zfill(2) for day in range(1, 32)],
            "time": [f"{hour:02d}:00" for hour in range(24)],
            "area": [lat + 0.01, lon - 0.01, lat - 0.01, lon + 0.01],
            "format": "netcdf",
        },
        target=tmp_file_path,
    )

    df = convert_nc_file_to_dataframe(source_file_path=tmp_file_path, limit=None)
    os.remove(tmp_file_path)

    if "expver" in df.columns:
        # merge expver 5 into empty expver 1
        df_expver1 = df[df["expver"] == 1].drop(columns=["expver"])
        df_expver5 = df[df["expver"] == 5].drop(columns=["expver"])

        tmp_df_combined = df_expver1.combine_first(df_expver5)

        df = tmp_df_combined

    df = df.rename(columns=RESPONSE_COLUMNS_MAPPING)
    df["surface_temperature"] = df["surface_temperature"] - 273.15

    df["time"] = pd.to_datetime(df["time"])
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df.drop(columns=["time"], inplace=True)
    df.sort_values(by=["latitude", "longitude", "year", "month"])
    df.reset_index(drop=True, inplace=True)
    columns = [*df.columns]
    columns.remove("year")
    columns.remove("month")
    columns = ["year", "month", *columns]
    df = df[columns]
    return df


def get_climate_data_of_years(lat: float, lon: float, years: list[int]) -> pd.DataFrame:
    result_df = pd.DataFrame()
    for year in years:
        df = get_climate_data_of_year(lat=lat, lon=lon, year=year)
        result_df = pd.concat([result_df, df], axis=0)
    result_df.reset_index(drop=True, inplace=True)
    return result_df


def main():
    # Example usage
    lat, lon = 40.211392, 16.682612  # Policoro
    years = [2013, 2016, 2018]

    df = get_climate_data_of_years(lat, lon, years)
    df[:100].to_csv("data/past_climate_example.csv")


if __name__ == "__main__":
    main()

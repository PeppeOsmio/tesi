from concurrent.futures import ThreadPoolExecutor
import io
import os
import random
import cdsapi
import asyncio

import pandas as pd
import xarray as xr


def __download_era5_data_sync(lat: float, lon: float, start_year: int, end_year: int):
    """
    Download ERA5 reanalysis data for a specific latitude and longitude from Copernicus Climate Data Store.

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

    tmp_file_path = f"{random.randbytes(32).hex()}.nc"
    result = c.retrieve(
        name="reanalysis-era5-single-levels-monthly-means",
        request={
            "product_type": "monthly_averaged_reanalysis",
            "variable": [
                "2m_temperature",
                "total_precipitation",
                "surface_solar_radiation_downwards",
                "2m_dewpoint_temperature",
                "mean_sea_level_pressure",
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
            ],
            "year": [str(year) for year in range(start_year, end_year + 1)],
            "month": [str(month).zfill(2) for month in range(1, 13)],
            "day": [str(day).zfill(2) for day in range(1, 32)],
            "time": [f"{hour:02d}:00" for hour in range(24)],
            "area": [lat + 0.01, lon - 0.01, lat - 0.01, lon + 0.01],
            "format": "netcdf",
            "expver": 1
        },
        target=tmp_file_path
    )
    # Load the data into an xarray Dataset directly from the binary stream
    ds = xr.open_dataset(tmp_file_path)
    # ds = ds.sel(expver=1)
    os.remove(tmp_file_path)
    df = ds.to_dataframe().reset_index()
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)
    df.sort_index()
    return df

async def download_era5_data(lat: float, lon: float, start_year: int, end_year: int) -> pd.DataFrame:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        df = await loop.run_in_executor(pool, __download_era5_data_sync, lat, lon, start_year, end_year)
    return df


async def main():
    # Example usage
    lat, lon = 40.71, -74.01  # New York City
    start_year = 2022
    end_year = 2024

    df = await download_era5_data(lat, lon, start_year, end_year)
    df.to_csv("data/copernicus_taranto.csv")

if __name__ == "__main__":
    asyncio.run(main())

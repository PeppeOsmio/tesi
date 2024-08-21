import asyncio
from concurrent.futures import ThreadPoolExecutor
import cdsapi
import pandas as pd
from tesi.database.di import get_session_maker
import xarray

from tesi.zappai.utils.common import convert_nc_file_to_dataframe

async def main():
    _ERA5_VARIABLES = {
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "2m_temperature",
        "evaporation",
        "total_precipitation",  # this can be derived by <mean_precipitation_flux> * <seconds in a day> / 1000 (to convert mm to m)
        "surface_pressure",
        "surface_solar_radiation_downwards",
        "surface_thermal_radiation_downwards",
        # exclusive to ERA5 below
        "surface_net_solar_radiation",
        "surface_net_thermal_radiation",
        "snowfall",
        "total_cloud_cover",
        "2m_dewpoint_temperature",
        "soil_temperature_level_3",
        "volumetric_soil_water_layer_3",
    }

    cds_client = cdsapi.Client(
        url="https://cds-beta.climate.copernicus.eu/api",
        key="01a739b2-eed9-4756-850a-564d0a2bb5f4",
    )

    cds_client.retrieve(
        name="reanalysis-era5-single-levels-monthly-means",
        request={
            "product_type": "monthly_averaged_reanalysis",
            "variable": list(_ERA5_VARIABLES),
            "year": [2009, 2010, 2011, 2012, 2013],
            "month": [str(month).zfill(2) for month in range(1, 13)],
            # "day": [str(day).zfill(2) for day in range(1, 32)],
            # "time": [f"{hour:02d}:00" for hour in range(24)],
            "time": ["00:00"],
            "format": "grib",
            "download_format": "unarchived",
            "area": [
                40 + 0.01,
                -90.8 - 0.01,
                40 - 0.01,
                -90.8 + 0.01,
            ],
        },
        target="test.grib",
    )

    session_maker = get_session_maker()

    async with session_maker() as session:
        def func():
            df = convert_nc_file_to_dataframe("./tmp/global_climate_data/dioporco.nc", None)
            df.to_csv("dioporco.csv")

        loop = asyncio.get_running_loop()
        
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(executor=pool, func=func)

if __name__ == "__main__":
    asyncio.run(main())

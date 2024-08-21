import asyncio
from concurrent.futures import ThreadPoolExecutor
import cdsapi
import pandas as pd
from tesi import logging_conf
from tesi.database.di import get_session_maker
import xarray

from tesi.zappai.utils.common import convert_nc_file_to_dataframe, process_copernicus_climate_data
from tesi.zappai.repositories.copernicus_data_store_api import _ERA5_VARIABLES, _ERA5_VARIABLES_RESPONSE_TO_DATAFRAME_MAPPING

async def main():

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
            "format": "netcdf",
            "download_format": "unarchived",
            "area": [
                40 + 0.01,
                -90.8 - 0.01,
                40 - 0.01,
                -90.8 + 0.01,
            ],
        },
        target="dioporco.nc",
    )

    session_maker = get_session_maker()

    async with session_maker() as session:
        def func():
            df = convert_nc_file_to_dataframe("dioporco.nc", None)
            df = process_copernicus_climate_data(df=df, columns_mappings=_ERA5_VARIABLES_RESPONSE_TO_DATAFRAME_MAPPING)
            df.to_csv("dioporco.csv")

        loop = asyncio.get_running_loop()
        
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(executor=pool, func=func)

if __name__ == "__main__":
    logging_conf.create_logger(config=logging_conf.get_default_conf())
    asyncio.run(main())

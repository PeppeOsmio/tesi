from datetime import datetime, timezone
import logging
import os
import random
from typing import Any, Callable
import cdsapi
import zipfile
import pandas as pd
from tesi.zappai.utils import common
from uuid import UUID
import shutil


ERA5_PARAMETERS = {
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
    "precipitation_type",
    "snowfall",
    "total_cloud_cover",
    "2m_dewpoint_temperature",
    "soil_temperature_level_1",
    "volumetric_soil_water_layer_1",
}

CMIP5_PARAMETERS = {
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "2m_temperature",
    "evaporation",
    "mean_precipitation_flux",
    "surface_pressure",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
}

ERA5_PARAMETERS_COLUMNS = {
    "u10": "10m_u_component_of_wind",  # Eastward component of wind at 10 meters
    "v10": "10m_v_component_of_wind",  # Northward component of wind at 10 meters
    "t2m": "2m_temperature",  # Temperature at 2 meters above the surface
    "e": "evaporation",  # Evaporation
    "ptype": "precipitation_type",  # Precipitation type (e.g., rain, snow)
    "tp": "total_precipitation",  # Total precipitation
    "sp": "surface_pressure",  # Surface pressure
    "ssrd": "surface_solar_radiation_downwards",  # Surface solar radiation downwards
    "strd": "surface_thermal_radiation_downwards",  # Surface thermal radiation downwards
    # Exclusive to ERA5 below
    "tcc": "total_cloud_cover",  # Total cloud cover
    "sf": "snowfall",  # Snowfall
    "d2m": "2m_dewpoint_temperature",  # Dewpoint temperature at 2 meters
    "stl1": "soil_temperature_level_1",  # Soil temperature at level 1 (top layer)
    "ssr": "surface_net_solar_radiation",  # Surface net solar radiation
    "str": "surface_net_thermal_radiation",  # Surface net thermal radiation
    "swvl1": "volumetric_soil_water_layer_1",  # Volumetric soil water content at layer 1
}


CMIP5_PARAMETERS_MAPPINGS = {
    "uas": "10m_u_component_of_wind",  # Eastward component of wind at 10 meters
    "vas": "10m_v_component_of_wind",  # Northward component of wind at 10 meters
    "tas": "2m_temperature",  # Temperature at 2 meters above the surface
    "evspsbl": "evaporation",  # Evaporation
    "pr": "mean_precipitation_flux",  # Precipitation flux
    "ps": "surface_pressure",  # Surface pressure
    "rsds": "surface_solar_radiation_downwards",  # Surface solar radiation downwards
    "rlds": "surface_thermal_radiation_downwards",  # Surface thermal radiation downwards
}

ERA5_RESULT_COLUMNS = {
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "2m_temperature",
    "evaporation",
    "precipitation_type",
    "total_precipitation",  # this can be derived by <mean_precipitation_flux> * <seconds in a day> / 1000 (to convert mm to m)
    "surface_pressure",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
    "surface_net_solar_radiation",
    "surface_net_thermal_radiation",
    # exclusive to ERA5 below
    "snowfall",
    "total_cloud_cover",
    "2m_dewpoint_temperature",
    "soil_temperature_level_1",
    "volumetric_soil_water_layer_1",
}

CMIP5_RESULT_COLUMNS = {
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "2m_temperature",
    "evaporation",
    "total_precipitation",
    "surface_pressure",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
}


class CopernicusDataStoreAPI:
    def __init__(self, user_id: int, api_token: UUID) -> None:
        self.cds_client = cdsapi.Client(
            url="https://cds.climate.copernicus.eu/api/v2",
            key=f"{user_id}:{api_token}",
            verify=1,
        )

    def get_future_climate_data(self) -> pd.DataFrame:
        """https://cds.climate.copernicus.eu/cdsapp#!/dataset/sis-hydrology-meteorology-derived-projections?tab=form

        Response headers:
            time lat lon bnds average_DT average_T1 average_T2 <parameter abbreviation> time_bnds lat_bnds lon_bnds

        Returns:
            pd.DataFrame:
        """
        dest_dir = "tmp/future_climate_data"

        os.makedirs(dest_dir, exist_ok=True)

        zip_file = os.path.join(dest_dir, f"{random.randbytes(16).hex()}.zip")

        self.cds_client.retrieve(
            "projections-cmip5-monthly-single-levels",
            {
                "ensemble_member": "r10i1p1",
                "format": "zip",
                "variable": list(CMIP5_PARAMETERS),
                "experiment": "historical",
                "model": "gfdl_cm2p1",
                "period": ["202101-202512"],
            },
            zip_file,
        )

        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(dest_dir)

        os.remove(zip_file)

        result_df = pd.DataFrame()

        for extracted_file in os.listdir(dest_dir):
            extracted_file_path = os.path.join(dest_dir, extracted_file)
            if not extracted_file.endswith(".nc"):
                continue
            logging.info(f"Converting {extracted_file_path}")
            df = common.convert_nc_file_to_dataframe(
                source_file_path=extracted_file_path, limit=None
            )
            # take only the first segment of each measurement for each day and location
            df = df[df["bnds"] == 1.0]
            df = df.drop(
                columns=[
                    "bnds",
                    "average_DT",
                    "average_T1",
                    "average_T2",
                    "time_bnds",
                    "lat_bnds",
                    "lon_bnds",
                ],
            )
            df = df.dropna()
            if "time" not in result_df.columns:
                result_df["time"] = df["time"]
            if "longitude" not in result_df.columns:
                result_df["longitude"] = df["lon"]
            if "latitude" not in result_df.columns:
                result_df["latitude"] = df["lat"]
            for key, value in CMIP5_PARAMETERS_MAPPINGS.items():
                if key in df.columns:
                    result_df[value] = df[key]
                    result_df.reset_index()
                    break
            os.remove(extracted_file_path)
        result_df = common.process_copernicus_climate_data(
            df=result_df, columns_mappings={}
        )

        # take only the FUTURE data
        now = datetime.now(tz=timezone.utc)
        result_df = result_df[
            (result_df.index.get_level_values("year") >= now.year)
            & (result_df.index.get_level_values("month") >= now.month)
        ]

        # convert from mm/s (aggregated over 24 hours) to m
        result_df["total_precipitation"] = (
            (result_df["mean_precipitation_flux"] / 1000) * 60 * 60 * 24
        )
        result_df = result_df.drop(columns=["mean_precipitation_flux"])

        return result_df

    def get_past_climate_data_for_years(
        self,
        longitude: float,
        latitude: float,
        years: list[int],
        on_save_chunk: Callable[[pd.DataFrame], None],
    ):

        tmp_dir = "./tmp/global_climate_data"
        os.makedirs(tmp_dir, exist_ok=True)

        _years = [*years]
        _years.sort()

        STEP = 15
        processed = 0

        while processed < len(_years):
            years_to_fetch = _years[processed : processed + STEP]

            logging.info(
                f"Getting data for years {years_to_fetch} and coordinates ({longitude} {latitude})"
            )
            tmp_file_path = os.path.join(tmp_dir, f"{random.randbytes(32).hex()}.nc")
            self.cds_client.retrieve(
                name="reanalysis-era5-single-levels-monthly-means",
                request={
                    "product_type": "monthly_averaged_reanalysis",
                    "variable": list(ERA5_PARAMETERS),
                    "year": [str(year) for year in years_to_fetch],
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

            if "expver" in tmp_df.columns:
                tmp_df = common.merge_by_expver(tmp_df)

            tmp_df = common.process_copernicus_climate_data(
                df=tmp_df, columns_mappings=ERA5_PARAMETERS_COLUMNS
            )
            on_save_chunk(tmp_df)
            processed += len(years_to_fetch)

            os.remove(tmp_file_path)

        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

    def get_past_climate_data(
        self,
        year_from: int | None,
        longitude: float,
        latitude: float,
        on_save_chunk: Callable[[pd.DataFrame], None],
    ):

        _year_from = year_from if year_from is not None else 1940

        now = datetime.now(tz=timezone.utc)

        if _year_from > now.year:
            return

        years = list(range(_year_from, now.year + 1))

        return self.get_past_climate_data_for_years(
            longitude=longitude,
            latitude=latitude,
            years=years,
            on_save_chunk=on_save_chunk,
        )


def main(): ...


if __name__ == "__main__":
    main()
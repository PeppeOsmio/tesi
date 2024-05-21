import logging
import os
import random
from typing import cast
import cdsapi
import zipfile

import pandas as pd
from tesi.climate.utility_scripts import common

RESPONSE_COLUMNS_MAPPING = {"lon": "longitude", "lat": "latitude"}


def download_future_climate_data() -> pd.DataFrame:
    """https://cds.climate.copernicus.eu/cdsapp#!/dataset/sis-hydrology-meteorology-derived-projections?tab=form

    Returns:
        pd.DataFrame: _description_
    """
    logging.basicConfig(level=logging.INFO)
    c = cdsapi.Client(
        url="https://cds.climate.copernicus.eu/api/v2",
        key="311032:15a4dd58-d44c-4d52-afa3-db18f38e1d2c",
        verify=1,
    )

    dest_dir = "tmp_future_climate"

    os.makedirs(dest_dir, exist_ok=True)

    zip_file = os.path.join(dest_dir, f"{random.randbytes(16).hex()}.zip")

    c.retrieve(
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

    result_df = common.process_copernicus_climate_data(df=result_df, columns_mappings=RESPONSE_COLUMNS_MAPPING)
    return result_df


if __name__ == "__main__":
    df = download_future_climate_data()
    df[:100].to_csv("data/future_climate_example.csv")
    os.makedirs("training_data", exist_ok=True)
    df.to_csv("training_data/future_climate.csv")

import argparse
import logging
from typing import cast
import pandas as pd
import xarray

# Policoro
EXAMPLE_LOCATION_COUNTRY = "Italy"
EXAMPLE_LOCATION_NAME = "Policoro"
EXAMPLE_LONGITUDE = 16.678341
EXAMPLE_LATITUDE = 40.212971


def coordinates_to_well_known_text(longitude: float, latitude: float) -> str:
    return f"POINT({longitude} {latitude})"


def convert_nc_file_to_dataframe(
    source_file_path: str, limit: int | None
) -> pd.DataFrame:
    ds = xarray.open_dataset(source_file_path)
    for name, index in ds.indexes.items():
        if isinstance(index, xarray.CFTimeIndex):
            ds[name] = index.to_datetimeindex()
    df = ds.to_dataframe()
    ds = None
    if limit is not None:
        df = df[:limit]
    df = df.reset_index()
    return df


def merge_by_expver(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Processing 'expver' column")
    df_expver1 = df[df["expver"] == 1].drop(columns=["expver"])
    df_expver5 = df[df["expver"] == 5].drop(columns=["expver"])

    logging.info(f"expver 1 DataFrame shape: {df_expver1.shape}")
    logging.info(f"expver 5 DataFrame shape: {df_expver5.shape}")

    df_combined = df_expver1.combine_first(df_expver5)

    logging.info(f"DataFrame shape after combining 'expver': {df.shape}")
    return df_combined


def process_copernicus_climate_data(
    df: pd.DataFrame, columns_mappings: dict[str, str]
) -> pd.DataFrame:
    logging.info(f"Initial DataFrame shape before processing: {df.shape}")

    # Renaming columns
    df = df.rename(columns=columns_mappings)
    logging.info(f"DataFrame shape after renaming columns: {df.shape}")

    # Converting and extracting date parts
    df["time"] = pd.to_datetime(df["time"])
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df = df.drop(columns=["time"])
    logging.info(
        f"DataFrame shape after time conversion and dropping 'time' column: {df.shape}"
    )

    # Resetting and setting index
    df = df.reset_index(drop=True)
    df = df.set_index(keys=["year", "month"])
    logging.info(f"DataFrame shape after setting index: {df.shape}")

    # Sorting index
    df = df.sort_index(ascending=[False, False])
    logging.info(f"DataFrame shape after sorting index: {df.shape}")

    return df

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


def process_copernicus_climate_data(
    df: pd.DataFrame, columns_mappings: dict[str, str]
) -> pd.DataFrame:

    df = df.dropna()

    # Renaming columns
    df = df.rename(columns=columns_mappings)

    # Converting and extracting date parts
    df["time"] = pd.to_datetime(df["time"])
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df = df.drop(columns=["time"])

    # Resetting and setting index
    df = df.reset_index(drop=True)
    df = df.set_index(keys=["year", "month"])

    # Sorting index
    df = df.sort_index(ascending=[True, True])
    df.to_csv("tmp/with_expver.csv")
    if "expver" in df.columns:
        
        df_expver1 = df[df["expver"] == 1].drop(columns=["expver"])
        df_expver5 = df[df["expver"] == 5].drop(columns=["expver"])

        df = df_expver1.combine_first(df_expver5)
        df.to_csv("tmp/without_expver.csv")

    return df

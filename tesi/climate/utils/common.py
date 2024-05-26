import argparse
from typing import cast
import pandas as pd
import xarray


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
    df.reset_index(inplace=True)
    return df


def process_copernicus_climate_data(
    df: pd.DataFrame, columns_mappings: dict[str, str]
) -> pd.DataFrame:
    df = df.rename(columns=columns_mappings)

    df["time"] = pd.to_datetime(df["time"])
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df.drop(columns=["time"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.set_index(keys=["year", "month"], inplace=True)
    df.sort_index(ascending=[True, True], inplace=True)
    if "expver" in df.columns:
        # merge expver 5 into empty expver 1
        df_expver1 = df[df["expver"] == 1].drop(columns=["expver"])
        df_expver5 = df[df["expver"] == 5].drop(columns=["expver"])
        tmp_df_combined = df_expver1.combine_first(df_expver5)
        df = tmp_df_combined

    return df




import argparse
import sys
from typing import cast
import pandas as pd
import xarray
import cftime


def convert_nc_file_to_dataframe(source_file_path: str, limit: int | None) -> pd.DataFrame:
    ds = xarray.open_dataset(source_file_path)
    df = ds.to_dataframe()
    for column in df.columns:
        if len(df) == 0:
            break
        if isinstance(df[column].iloc[0], cftime.datetime):
            df[column] = pd.to_datetime(df[column].astype(str))
    ds = None
    if limit is not None:
        df = df[:limit]
    df.reset_index(inplace=True)
    return df

def process_copernicus_climate_data(df: pd.DataFrame, columns_mappings: dict[str, str]) -> pd.DataFrame:
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


if __name__ == "__main__":
    # Create the ArgumentParser object
    parser = argparse.ArgumentParser(
        description="Process a file path and an optional limit."
    )

    # Add the file path argument
    parser.add_argument("--path", type=str, help="The path to the file.")

    # Add the limit argument
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        required=False,
        help="An optional limit on the number of items.",
    )

    # Parse the arguments
    args = parser.parse_args()

    file_to_convert = cast(str, args.path)
    limit = cast(int | None, args.limit)

    df = convert_nc_file_to_dataframe(source_file_path=file_to_convert, limit=limit)
    df.to_csv(file_to_convert + ".csv")
    print(df)

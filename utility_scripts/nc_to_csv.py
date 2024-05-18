import argparse
import sys
from typing import cast
import xarray


def convert(source_file_path: str, dest_file_path: str, limit: int | None):
    ds = xarray.load_dataset(source_file_path)
    df = ds.to_dataframe()
    ds = None
    if limit is not None:
        df = df[:limit]
    df.reset_index()
    if "time" in df.columns:
        df.set_index("time", inplace=True)
        df.sort_index()
    df.to_csv(dest_file_path)


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

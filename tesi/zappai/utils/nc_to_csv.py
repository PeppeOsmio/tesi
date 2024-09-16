import argparse
from typing import cast

from tesi.zappai.utils.common import convert_nc_file_to_dataframe

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

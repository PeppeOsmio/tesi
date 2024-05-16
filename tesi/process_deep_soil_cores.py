import os
from typing import Literal
import pandas as pd

XLSX_PATH = "data/13_year_corn/xlsx/Field 70-71 Deep Soil Cores 2012-2017_0.xlsx"
OUTPUT_PATH = "data/processed_csvs/deep_soil_cores"

Depth = Literal["0 to 15", "15 to 30", "30 to 60", "60 to 90", "90 to 120"]


def process_sheet_of_year(output_path: str, xlsx_path: str, year: Literal["2012", "2016", "2017"]):
    os.makedirs(output_path, exist_ok=True)

    deep_soil_df = pd.read_excel(
        xlsx_path,
        sheet_name=f"Field 70-71 {year}",
    )
    field_70_dict: dict[Depth, pd.DataFrame] = {
        "0 to 15": pd.DataFrame(columns=deep_soil_df.columns),
        "15 to 30": pd.DataFrame(columns=deep_soil_df.columns),
        "30 to 60": pd.DataFrame(columns=deep_soil_df.columns),
        "60 to 90": pd.DataFrame(columns=deep_soil_df.columns),
        "90 to 120": pd.DataFrame(columns=deep_soil_df.columns),
    }

    field_71_dict: dict[Depth, pd.DataFrame] = {
        "0 to 15": pd.DataFrame(columns=deep_soil_df.columns),
        "15 to 30": pd.DataFrame(columns=deep_soil_df.columns),
        "30 to 60": pd.DataFrame(columns=deep_soil_df.columns),
        "60 to 90": pd.DataFrame(columns=deep_soil_df.columns),
        "90 to 120": pd.DataFrame(columns=deep_soil_df.columns),
    }

    # Enumerate and conditionally add rows to the respective DataFrames
    for i, row in deep_soil_df.iterrows():
        if not isinstance(i, int):
            raise TypeError("index must be an int")
        df: pd.DataFrame | None = None
        depth: Depth = "0 to 15"
        field: Literal[70, 71] = 70
        if i % 10 == 0:
            depth = "0 to 15"
            field = 70
        elif i % 10 == 1:
            depth = "15 to 30"
            field = 70
        elif i % 10 == 2:
            depth = "30 to 60"
            field = 70
        elif i % 10 == 3:
            depth = "60 to 90"
            field = 70
        elif i % 10 == 4:
            depth = "90 to 120"
            field = 70
        elif i % 10 == 5:
            depth = "0 to 15"
            field = 71
        elif i % 10 == 6:
            depth = "15 to 30"
            field = 71
        elif i % 10 == 7:
            depth = "30 to 60"
            field = 71
        elif i % 10 == 8:
            depth = "60 to 90"
            field = 71
        elif i % 10 == 9:
            depth = "90 to 120"
            field = 71
        if field == 70:
            df = field_70_dict[depth]
            field_70_dict[depth] = pd.concat([df, row.to_frame().T], ignore_index=True)
        elif field == 71:
            df = field_71_dict[depth]
            field_71_dict[depth] = pd.concat([df, row.to_frame().T], ignore_index=True)


    for depth, df in field_70_dict.items():
        df.to_csv(os.path.join(output_path, f'field_70_{depth.replace(" ", "_")}.csv'))

    for depth, df in field_71_dict.items():
        df.to_csv(os.path.join(output_path, f'field_71_{depth.replace(" ", "_")}.csv'))

for year in ("2012", "2016", "2017"):
    process_sheet_of_year(output_path=OUTPUT_PATH, xlsx_path=XLSX_PATH, year=year)
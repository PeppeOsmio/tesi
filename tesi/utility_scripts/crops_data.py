import os
from typing import cast
import pandas as pd
import requests
from io import StringIO

all_columns = [
    "Author",
    "Journal",
    "Year",
    "Site country",
    "Location",
    "Latitude",
    "Longitude",
    "Soil information recorded in the paper",
    "pH (surface layer)",
    "Replications in experiment",
    "Crop",
    "Initial year of NT practice ( or first year of experiment if missing)",
    "Sowing year",
    "Harvest year",
    "Years since NT started (yrs)",
    "Crop growing season recorded in the paper",
    "Crop rotation with at least 3 crops involved in CT",
    "Crop rotation with at least 3 crops involved in NT",
    "Crop sequence (details)",
    "Cover crop before sowing",
    "Soil cover in CT",
    "Soil cover in NT",
    "Residue management of previous crop in CT  (details)",
    "Residue management of previous crop in NT (details)",
    "Weed and pest control CT",
    "Weed and pest control NT ",
    "Weed and pest control CT (details)",
    "Weed and pest control NT  (details)",
    "Fertilization CT ",
    "Fertilization NT",
    "N input",
    "N input rates with the unit kg N ha-1 (details)",
    "Field fertilization (details)",
    "Irrigation CT",
    "Irrigation NT",
    "Water applied in CT",
    "Water applied in NT",
    "Other information",
    "Yield of CT",
    "Yield of NT",
    "Relative yield change",
    "Yield increase with NT",
    "Outlier of CT",
    "Outlier of NT",
    "Sowing month",
    "Harvesting month",
    "P",
    "E",
    "PB",
    "Tave",
    "Tmax",
    "Tmin",
    "ST",
]


columns_to_include: dict[str, str] = {
    "Site country": "country",
    "Location": "location",
    "Latitude": "latitude",
    "Longitude": "longitude",
    # "Soil information recorded in the paper": "soil",
    "pH (surface layer)": "ph",
    "Crop": "crop",
    "Sowing year": "sowing_year",
    "Sowing month": "sowing_month",
    "Harvest year": "harvest_year",
    "Harvesting month": "harvest_month",
    # "Yield of CT": "yield_ct",
    "Yield of NT": "yield",
    # "P": "P",
    # "E": "E",
    # "PB": "PB",
    # "Tave": "Tave",
    # "Tmax": "Tmax",
    # "Tmin": "Tmin",
    # "ST": "ST",
}


def download_crops_yield_data() -> pd.DataFrame:
    dest_folder = "data/crops_data"

    os.makedirs(dest_folder, exist_ok=True)

    url = "https://figshare.com/ndownloader/files/26690678"

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Can't fetch crop database from {url}. Status {response.status_code}, details {response.text}")

    df = pd.read_csv(
        StringIO(initial_value=response.text), usecols=list(columns_to_include.keys())
    )
    df = df.filter(items=list(columns_to_include.keys())).rename(
        columns=columns_to_include
    )

    df.sort_values(by=["crop", "country", "location"], ascending=[True, True, True])

    df.reset_index(drop=True, inplace=True)
    return df


if __name__ == "__main__":
    df = download_crops_yield_data()
    df[:100].to_csv("data/crops_example.csv")

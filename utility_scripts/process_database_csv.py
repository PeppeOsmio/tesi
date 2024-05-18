import os
from typing import cast
import pandas as pd

columns = [
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
    "Soil information recorded in the paper": "soil",
    "pH (surface layer)": "pH",
    "Crop": "crop",
    "Sowing year": "sowing_year",
    "Sowing month": "sowing_month",
    "Harvest year": "harvest_year",
    "Harvesting month": "harvest_month",
    "Yield of CT": "yield_ct",
    "Yield of NT": "yield_nt",
    "P": "P",
    "E": "E",
    "PB": "PB",
    "Tave": "Tave",
    "Tmax": "Tmax",
    "Tmin": "Tmin",
    "ST": "ST",
}


def main():
    dest_folder = "data/crops_data"

    os.makedirs(dest_folder, exist_ok=True)

    df = pd.read_csv(
        "data/raw_data/Database.csv", usecols=list(columns_to_include.keys())
    )
    df = df.filter(items=list(columns_to_include.keys())).rename(
        columns=columns_to_include
    )

    crops = set(cast(list[str], df["crop"]))

    for crop in crops:
        crop_folder = os.path.join(dest_folder, crop)
        os.makedirs(crop_folder, exist_ok=True)

        crop_df = df[df["crop"] == crop]
        crop_df = crop_df.sort_values(
            by=["country", "location", "soil"], ascending=[True, True, True]
        )
        crop_df.reset_index(inplace=True)

        crop_df.to_csv(os.path.join(crop_folder, f"{crop}.csv"))


if __name__ == "__main__":
    main()

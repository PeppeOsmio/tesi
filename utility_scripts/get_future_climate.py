import logging
import os
import random
import cdsapi
import zipfile
from tesi.utility_scripts import nc_to_csv

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    c = cdsapi.Client(
        url="https://cds.climate.copernicus.eu/api/v2",
        key="311032:15a4dd58-d44c-4d52-afa3-db18f38e1d2c",
        verify=1,
    )

    dest_dir = "data/future_climate"

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

    for extracted_file in os.listdir(dest_dir):
        extracted_file_path = os.path.join(dest_dir, extracted_file)
        if not extracted_file.endswith(".nc"):
            continue
        csv_path = ""
        if extracted_file.startswith("prAdjust"):
            csv_path = os.path.join(dest_dir, "precipitations.csv")
        elif extracted_file.startswith("tasAdjust"):
            csv_path = os.path.join(dest_dir, "temperature_at_surface.csv")
        logging.info(f"Converting {extracted_file_path} to {csv_path}")
        nc_to_csv.convert(source_file_path=extracted_file_path, dest_file_path=csv_path, limit=None)
        os.remove(extracted_file_path)

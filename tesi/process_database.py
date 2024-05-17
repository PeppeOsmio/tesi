import pandas as pd

df = pd.read_csv("data/Database.csv")

columns_to_pop = [
    "Other information",
    "Author",
    "Journal",
    "Replications in experiment",
    "Initial year of NT practice ( or first year of experiment if missing)",
    "Years since NT started (yrs)",
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
    "Irrigation CT",
    "Irrigation NT",
    "Water applied in CT",
    "Water applied in NT",
    "Outlier of CT",
    "Outlier of NT",
    "Yield increase with NT",
    "Relative yield change",
    "Field fertilization (details)",
    "N input rates with the unit kg N ha-1 (details)",
    "N input",
    "Fertilization NT",
    "Fertilization CT ",
    "Crop growing season recorded in the paper"
]

for column in columns_to_pop:
    df.pop(column)

df.to_csv("data/Database_processed.csv")

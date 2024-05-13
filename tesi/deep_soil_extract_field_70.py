import pandas as pd

deep_soil_df = pd.read_excel(
    "data/13_year_corn/xlsx/Field 70-71 Deep Soil Cores 2012-2017_0.xlsx",
    sheet_name="Field 70-71 2017",
)

deep_soil_df

for item in deep_soil_df.values[:30]:
    print(item)

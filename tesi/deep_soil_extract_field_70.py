import pandas as pd

deep_soil_df = pd.read_excel(
    "data/13_year_corn/xlsx/Field 70-71 Deep Soil Cores 2012-2017_0.xlsx",
    sheet_name="Field 70-71 2017",
)


# Field 70
field_70_2017_0_to_15_df = pd.DataFrame(columns=deep_soil_df.columns)
field_70_2017_

field_71_2017_0_to_15_df = pd.DataFrame(columns=deep_soil_df.columns)


# Enumerate and conditionally add rows to the respective DataFrames
for i, row in deep_soil_df.iterrows():
    if i % 2 == 0:
        field_70_deep_soil_df = pd.concat(
            [field_70_deep_soil_df, row.to_frame().T], ignore_index=True
        )
    else:
        field_71_deep_soil_df = pd.concat(
            [field_71_deep_soil_df, row.to_frame().T], ignore_index=True
        )

field_70_deep_soil_df.to_csv(path_or_buf="field_70_2017_0_to_15.csv")
field_71_deep_soil_df.to_csv(path_or_buf="field_71_2017_0_to_15.csv")

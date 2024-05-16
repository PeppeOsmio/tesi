import pandas as pd

df = pd.read_csv("data/Database.csv")
df.pop("Other information")
df.to_csv("data/Database_processed.csv")
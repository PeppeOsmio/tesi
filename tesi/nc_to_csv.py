import sys
import xarray



if len(sys.argv) < 2:
    raise SyntaxError("expected file path arg")

file_to_convert = sys.argv[1]

ds = xarray.load_dataset(file_to_convert)
df = ds.to_dataframe()
df.reset_index()
if "time" in df.columns:
    df.set_index("time", inplace=True)
    df.sort_index()
df.to_csv(file_to_convert + ".csv")

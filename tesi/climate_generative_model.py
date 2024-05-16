from tesi import nasa_power_api
import asyncio

TARANTO_LAT = 40.464361
TARANTO_LON = 17.247030


async def main():
    climate_data = await nasa_power_api.get_nasa_power_climate_data(
        lat=TARANTO_LAT, lon=TARANTO_LON, start_year=1981, end_year=2022
    )
    climate_data.to_csv("data/taranto.csv")

    model_df = climate_data
    for parameter in nasa_power_api.CLIMATE_PARAMETERS:
        for i in range(5):
            climate_data[f"{parameter}_{i+1}_months_ago"] = climate_data[
                parameter
            ].shift(i + 1)


if __name__ == "__main__":
    asyncio.run(main())

import aiohttp
import pandas as pd
import json
import asyncio


async def get_nasa_power_climate_data(
    lat: float, lon: float, start_year: int, end_year: int
) -> pd.DataFrame:
    """Gets historical monthly climate data for given latitude/longitude from NASA POWER.
    https://power.larc.nasa.gov/#resources

    1. T2M: Average Temperature at 2 meters
        Description: This is the average air temperature measured at a height of 2 meters above the ground.
        Units: Degrees Celsius (°C)

    2. T2M_MAX: Maximum Temperature at 2 meters
        Description: This is the highest air temperature recorded at a height of 2 meters above the ground for the given time period.
        Units: Degrees Celsius (°C)

    3. T2M_MIN: Minimum Temperature at 2 meters
        Description: This is the lowest air temperature recorded at a height of 2 meters above the ground for the given time period.
        Units: Degrees Celsius (°C)

    4. PRECTOTCORR: Corrected Precipitation
        Description: This is the total amount of precipitation (rain, snow, etc.) corrected for any known measurement errors.
        Units: Millimeters (mm)

    5. ALLSKY_SFC_SW_DWN: All-Sky Surface Shortwave Downward Irradiance
        Description: This measures the total amount of solar energy reaching the Earth's surface from the sun, including when the sky is clear or cloudy.
        Units: Megajoules per square meter per day (MJ/m²/day)

    6. CLRSKY_SFC_SW_DWN: Clear-Sky Surface Shortwave Downward Irradiance
        Description: This measures the amount of solar energy reaching the Earth's surface from the sun when the sky is clear (no clouds).
        Units: Megajoules per square meter per day (MJ/m²/day)

    7. RH2M: Relative Humidity at 2 meters
        Description: This is the amount of moisture in the air at a height of 2 meters, expressed as a percentage of the maximum moisture the air can hold at that temperature.
        Units: Percent (%)

    8. WS2M: Wind Speed at 2 meters
        Description: This is the average speed of the wind measured at a height of 2 meters above the ground.
        Units: Meters per second (m/s)

    9. PS: Surface Pressure
        Description: This is the atmospheric pressure at the Earth's surface.
        Units: Kilopascals (kPa)

    10. QV2M: Specific Humidity at 2 meters
        Description: This is the mass of water vapor present in a kilogram of air, measured at a height of 2 meters.
        Units: Grams of water vapor per kilogram of air (g/kg)

    11. DISPH: Days with Precipitation > 1mm
        Description: This is the number of days during the given time period where the total precipitation was greater than 1 millimeter.
        Units: Days

    Args:
        lat (float):
        lon (float):
        start_year (int):
        end_year (int):

    Raises:
        SyntaxError:
        Exception:

    Returns:
        DataFrame:
    """
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"

    parameters_to_get = [
        "T2M",
        "T2M_MAX",
        "T2M_MIN",
        "PRECTOTCORR",
        "ALLSKY_SFC_SW_DWN",
        "CLRSKY_SFC_SW_DWN",
        "RH2M",
        "WS2M",
        "PS",
        "QV2M",
        "DISPH",
    ]
    params = {
        "latitude": lat,
        "longitude": lon,
        "start": start_year,
        "end": end_year,
        "community": "ag",
        "parameters": ",".join(parameters_to_get),
        "format": "JSON",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, params=params) as response:
            data = await response.json()

    if response.status != 200:
        if response.status == 422:
            raise SyntaxError(f"{response.status}: {json.dumps(data)}")
        else:
            raise Exception(f"{response.status}: {json.dumps(data)}")

    with open("nasa_response.json", "w") as file:
        file.write(json.dumps(data, indent=4))

    # Estrazione dei dati e conversione in DataFrame
    records = []
    for yearmonth in data["properties"]["parameter"]["T2M"]:
        record = {
            "year": int(yearmonth[:4]),
            "month": int(yearmonth[4:]),
        }
        for parameter in parameters_to_get:
            record.update(
                {parameter: data["properties"]["parameter"][parameter][yearmonth]}
            )
        records.append(record)

    df = pd.DataFrame(records)
    return df


async def main():
    # Esempio di utilizzo
    lat, lon = 40.16, 16.65
    start_year = 2017
    end_year = 2017

    nasa_power_data = await get_nasa_power_climate_data(lat, lon, start_year, end_year)
    print(nasa_power_data)


if __name__ == "__main__":
    asyncio.run(main())

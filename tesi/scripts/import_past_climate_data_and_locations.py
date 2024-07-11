import asyncio

from tesi.database.di import get_session_maker
from tesi.zappai.di import get_cds_api, get_crop_repository, get_crop_yield_data_repository, get_location_repository, get_past_climate_data_repository

async def main():
    session_maker = get_session_maker()
    location_repository = get_location_repository(session_maker=session_maker)
    cds_api = get_cds_api()
    past_climate_data_repository = get_past_climate_data_repository(
        session_maker=session_maker,
        cds_api=cds_api,
        location_repository=location_repository,
    )
    await location_repository.import_from_csv()
    await past_climate_data_repository.import_from_csv()


if __name__ == "__main__":
    asyncio.run(main())
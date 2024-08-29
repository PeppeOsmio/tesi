from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, cast
from uuid import UUID
import uuid
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from tesi.zappai.exceptions import LocationNotFoundError, SoilTypeNotFoundError
from tesi.zappai.dtos import LocationDTO, SoilTypeDTO
from tesi.zappai.models import Location
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import pandas as pd
import asyncio
from csv import DictWriter


class LocationRepository:
    def __init__(
        self,
    ) -> None:
        pass

    async def delete_location(self, session: AsyncSession, location_id: UUID):
        stmt = delete(Location).where(Location.id == location_id)
        await session.execute(stmt)

    async def create_location(
        self,
        session: AsyncSession,
        country: str,
        name: str,
        longitude: float,
        latitude: float,
    ) -> LocationDTO:
        location_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        stmt = insert(Location).values(
            id=location_id,
            country=country,
            name=name,
            longitude=longitude,
            latitude=latitude,
            created_at=now,
            is_downloading_past_climate_data=False
        )
        await session.execute(stmt)
        return LocationDTO(
            id=location_id,
            country=country,
            name=name,
            longitude=longitude,
            latitude=latitude,
            created_at=now,
            is_downloading_past_climate_data=False
        )
    
    async def set_locations_to_not_downloading(self, session: AsyncSession):
        stmt = update(Location).values(is_past_climate_data_downloading=True)
        await session.execute(stmt)

    async def get_locations(self, session: AsyncSession) -> list[LocationDTO]:
        stmt = select(Location).order_by(Location.created_at)
        locations = await session.scalars(stmt)
        return [self.__location_model_to_dto(location) for location in locations]

    async def get_location_by_country_and_name(
        self, session: AsyncSession, country: str, name: str
    ) -> LocationDTO | None:
        stmt = select(Location).where(
            (Location.country == country) & (Location.name == name)
        )
        location = await session.scalar(stmt)
        if location is None:
            return None
        return self.__location_model_to_dto(location)

    async def get_location_by_id(
        self, session: AsyncSession, location_id: UUID
    ) -> LocationDTO | None:
        stmt = select(Location).where(Location.id == location_id)
        location = await session.scalar(stmt)
        if location is None:
            return None
        return self.__location_model_to_dto(location)

    async def get_location_by_coordinates(
        self, session: AsyncSession, longitude: float, latitude: float
    ) -> LocationDTO | None:
        stmt = select(Location).where(
            (Location.longitude == longitude) & (Location.latitude == latitude)
        )
        location = await session.scalar(stmt)
        if location is None:
            return None
        return self.__location_model_to_dto(location)

    async def export_to_csv(
        self,
        session: AsyncSession,
        csv_path: str,
        location_ids: list[UUID],
    ):

        def open_csv_file():
            return open(csv_path, "w")

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            csv_file = await loop.run_in_executor(executor=pool, func=open_csv_file)
            with csv_file:
                stmt = select(Location).where(Location.id.in_(location_ids))
                results = list(await session.scalars(stmt))
                if len(results) == 0:
                    raise LocationNotFoundError(f"No locations found")
                locations = [self.__location_model_to_dto(model) for model in results]
                dicts: list[dict[str, Any]] = []
                for location in locations:
                    dct = location.to_dict()
                    dct.pop("id")
                    dicts.append(dct)

                def write_to_csv():
                    csv_writer = DictWriter(f=csv_file, fieldnames=dicts[0].keys())
                    csv_writer.writeheader()
                    csv_writer.writerows(dicts)

                await loop.run_in_executor(executor=pool, func=write_to_csv)

    async def import_from_csv(self, session: AsyncSession, csv_path: str):
        def read_csv() -> pd.DataFrame:
            return pd.read_csv(csv_path, parse_dates=["created_at"])

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            data = await loop.run_in_executor(executor=pool, func=read_csv)

        dicts = cast(list[dict[str, Any]], data.to_dict(orient="records"))
        for dct in dicts:
            await session.execute(
                delete(Location).where(
                    (Location.name == dct["name"])
                    & (Location.country == dct["country"])
                )
            )
            stmt = insert(Location).values(id=uuid.uuid4(), **dct)
            await session.execute(stmt)

    def __location_model_to_dto(self, location: Location) -> LocationDTO:
        return LocationDTO(
            id=location.id,
            country=location.country,
            name=location.name,
            longitude=location.longitude,
            latitude=location.latitude,
            created_at=location.created_at,
            is_downloading_past_climate_data=location.is_downloading_past_climate_data
        )

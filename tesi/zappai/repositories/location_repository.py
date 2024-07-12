from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, cast
from uuid import UUID
import uuid
from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from tesi.zappai.common import get_or_create_event_loop
from tesi.zappai.exceptions import LocationNotFoundError
from tesi.zappai.repositories.dtos import LocationDTO
from tesi.zappai.models import Location
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import pandas as pd
import asyncio
from csv import DictWriter


class LocationRepository:
    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session_maker = session_maker

    async def delete_location(self, name: str):
        async with self.session_maker() as session:
            stmt = delete(Location).where(Location.name == name)
            await session.execute(stmt)
            await session.commit()

    async def create_location(
        self, country: str, name: str, longitude: float, latitude: float
    ) -> LocationDTO:
        location_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        async with self.session_maker() as session:
            stmt = insert(Location).values(
                id=location_id,
                country=country,
                name=name,
                longitude=longitude,
                latitude=latitude,
                created_at=now,
            )
            await session.execute(stmt)
            await session.commit()
        return LocationDTO(
            id=location_id,
            country=country,
            name=name,
            longitude=longitude,
            latitude=latitude,
            created_at=now,
        )

    async def get_location_by_country_and_name(
        self, country: str, name: str
    ) -> LocationDTO | None:
        async with self.session_maker() as session:
            stmt = select(Location).where(
                (Location.country == country) & (Location.name == name)
            )
            location = await session.scalar(stmt)
        if location is None:
            return None
        return self.__location_model_to_dto(location)

    async def get_location_by_id(self, location_id: UUID) -> LocationDTO | None:
        async with self.session_maker() as session:
            stmt = select(Location).where(Location.id == location_id)
            location = await session.scalar(stmt)
        if location is None:
            return None
        return self.__location_model_to_dto(location)

    async def get_location_by_coordinates(
        self, longitude: float, latitude: float
    ) -> LocationDTO | None:
        async with self.session_maker() as session:
            stmt = select(Location).where(
                (Location.longitude == longitude) & (Location.latitude == latitude)
            )
            location = await session.scalar(stmt)
        if location is None:
            return None
        return self.__location_model_to_dto(location)

    async def export_to_csv(
        self,
        csv_path: str,
        location_ids: list[UUID],
    ):

        def open_csv_file():
            return open(csv_path, "w")

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            csv_file = await loop.run_in_executor(executor=pool, func=open_csv_file)
            with csv_file:
                async with self.session_maker() as session:
                    stmt = select(Location).where(Location.id.in_(location_ids))
                    results = list(await session.scalars(stmt))
                if len(results) == 0:
                    raise LocationNotFoundError(f"No locations found")
                locations = [self.__location_model_to_dto(model) for model in results]
                dicts = [location.to_dict() for location in locations]

                def write_to_csv():
                    csv_writer = DictWriter(f=csv_file, fieldnames=dicts[0].keys())
                    csv_writer.writeheader()
                    csv_writer.writerows(dicts)

                await loop.run_in_executor(executor=pool, func=write_to_csv)

    async def import_from_csv(self, csv_path: str):
        def read_csv() -> pd.DataFrame:
            return pd.read_csv(csv_path, parse_dates=["created_at"])

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            data = await loop.run_in_executor(executor=pool, func=read_csv)

        async with self.session_maker() as session:
            dicts = cast(list[dict[str, Any]], data.to_dict(orient="records"))
            for dct in dicts:
                location = await session.scalar(select(Location.id).where(Location.id == dct["id"])) 
                if location is not None:
                    continue
                stmt = insert(Location).values(**dct)
                await session.execute(stmt)
                await session.commit()

    def __location_model_to_dto(self, location: Location) -> LocationDTO:
        return LocationDTO(
            id=location.id,
            country=location.country,
            name=location.name,
            longitude=location.longitude,
            latitude=location.latitude,
            created_at=location.created_at,
        )

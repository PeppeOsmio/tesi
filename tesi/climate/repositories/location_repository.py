from datetime import datetime, timezone
from uuid import UUID
import uuid
from sqlalchemy import delete, insert, select
from tesi.climate.dtos import LocationDTO
from tesi.climate.models import Location
from sqlalchemy.ext.asyncio import AsyncSession


class LocationRepository:
    def __init__(
        self,
        db_session: AsyncSession,
    ) -> None:
        self.db_session = db_session

    async def delete_location(self, name: str):
        async with self.db_session as session:
            stmt = delete(Location).where(Location.name == name)
            await session.execute(stmt)
            await session.commit()

    async def create_location(
        self, country: str, name: str, longitude: float, latitude: float
    ) -> LocationDTO:
        location_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        async with self.db_session as session:
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
        async with self.db_session as session:
            stmt = select(Location).where(
                (Location.country == country) & (Location.name == name)
            )
            location = await session.scalar(stmt)
        if location is None:
            return None
        return self.__location_model_to_dto(location)

    async def get_location_by_id(self, location_id: UUID) -> LocationDTO | None:
        async with self.db_session as session:
            stmt = select(Location).where(Location.id == location_id)
            location = await session.scalar(stmt)
        if location is None:
            return None
        return self.__location_model_to_dto(location)

    async def get_location_by_coordinates(
        self, longitude: float, latitude: float
    ) -> LocationDTO | None:
        async with self.db_session as session:
            stmt = select(Location).where(
                (Location.longitude == longitude) & (Location.latitude == latitude)
            )
            location = await session.scalar(stmt)
        if location is None:
            return None
        return self.__location_model_to_dto(location)

    def __location_model_to_dto(self, location: Location) -> LocationDTO:
        return LocationDTO(
            id=location.id,
            country=location.country,
            name=location.name,
            longitude=location.longitude,
            latitude=location.latitude,
            created_at=location.created_at,
        )
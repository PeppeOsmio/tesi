from datetime import datetime, timezone
import uuid
from sqlalchemy import insert, select
from tesi.zappai.repositories.dtos import CropDTO
from tesi.zappai.models import Crop
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class CropRepository:
    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session_maker = session_maker

    async def create_crop(self, name: str) -> CropDTO:
        crop_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        async with self.session_maker() as session:
            stmt = insert(Crop).values(
                [{"id": crop_id, "name": name, "created_at": now}]
            )
            await session.execute(stmt)
            await session.commit()
        return CropDTO(id=crop_id, name=name, created_at=now)

    async def get_crop_by_name(self, name: str) -> CropDTO | None:
        async with self.session_maker() as session:
            stmt = select(Crop).where(Crop.name == name)
            crop = await session.scalar(stmt)
        if crop is None:
            return None
        return self.__crop_model_to_dto(crop)

    async def get_crop_by_id(self, crop_id: uuid.UUID) -> CropDTO | None:
        async with self.session_maker() as session:
            stmt = select(Crop).where(Crop.id == crop_id)
            crop = await session.scalar(stmt)
        if crop is None:
            return None
        return CropDTO(id=crop.id, name=crop.name, created_at=crop.created_at)

    def __crop_model_to_dto(self, crop: Crop) -> CropDTO:
        return CropDTO(id=crop.id, name=crop.name, created_at=crop.created_at)

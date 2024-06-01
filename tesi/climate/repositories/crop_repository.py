from datetime import datetime, timezone
import uuid
from sqlalchemy import insert, select
from tesi.climate.dtos import CropDTO
from tesi.climate.models import Crop
from sqlalchemy.ext.asyncio import AsyncSession


class CropRepository:
    def __init__(
        self,
        db_session: AsyncSession,
    ) -> None:
        self.db_session = db_session

    async def create_crop(self, name: str) -> CropDTO:
        crop_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        async with self.db_session as session:
            stmt = insert(Crop).values(
                [{"id": crop_id, "name": name, "created_at": now}]
            )
            await session.execute(stmt)
            await session.commit()
        return CropDTO(id=crop_id, name=name, created_at=now)

    async def get_crop_by_name(self, name: str) -> CropDTO | None:
        async with self.db_session as session:
            stmt = select(Crop).where(Crop.name == name)
            crop = await session.scalar(stmt)
        if crop is None:
            return None
        return self.__crop_model_to_dto(crop)

    def __crop_model_to_dto(self, crop: Crop) -> CropDTO:
        return CropDTO(id=crop.id, name=crop.name, created_at=crop.created_at)

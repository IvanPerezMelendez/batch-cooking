import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.tag import Tag
from .base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Tag, db)

    async def get_by_name(self, name: str) -> Tag | None:
        result = await self.db.execute(select(Tag).where(Tag.name == name))
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: list[uuid.UUID]) -> list[Tag]:
        result = await self.db.execute(select(Tag).where(Tag.id.in_(ids)))
        return list(result.scalars().all())

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.settings import Settings
from .base import BaseRepository


class SettingsRepository(BaseRepository[Settings]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Settings, db)

    async def get_by_key(self, key: str) -> Settings | None:
        result = await self.db.execute(select(Settings).where(Settings.key == key))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Settings]:
        result = await self.db.execute(select(Settings).order_by(Settings.key))
        return list(result.scalars().all())

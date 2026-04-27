from typing import Any

from ..models.settings import Settings
from ..repositories.settings import SettingsRepository
from .base import BaseService
from .schemas import SettingsCreate, SettingsUpdate


class SettingsService(BaseService[Settings, SettingsRepository, SettingsCreate, SettingsUpdate]):
    def __init__(self, repository: SettingsRepository) -> None:
        super().__init__(repository)

    async def get(self, key: str) -> Any:
        setting = await self.repository.get_by_key(key)
        return setting.value if setting else None

    async def set(self, data: SettingsCreate) -> Settings:
        existing = await self.repository.get_by_key(data.key)
        if existing:
            existing.value = data.value
            return await self.repository.update(existing)
        return await self.repository.create(Settings(key=data.key, value=data.value))

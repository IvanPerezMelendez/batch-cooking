from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...repositories.settings import SettingsRepository
from ..settings import SettingsService


def get_settings_service_from_session(session: AsyncSession) -> SettingsService:
    return SettingsService(SettingsRepository(session))


async def get_settings_service(
    session: AsyncSession = Depends(get_db),
) -> SettingsService:
    return get_settings_service_from_session(session)

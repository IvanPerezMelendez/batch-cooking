from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...repositories.tag import TagRepository
from ..tag import TagService


def get_tag_service_from_session(session: AsyncSession) -> TagService:
    return TagService(TagRepository(session))


async def get_tag_service(
    session: AsyncSession = Depends(get_db),
) -> TagService:
    return get_tag_service_from_session(session)

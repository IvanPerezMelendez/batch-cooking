import uuid

from ..models.tag import Tag
from ..repositories.tag import TagRepository
from .base import BaseService
from .schemas import TagCreate, TagUpdate


class TagService(BaseService[Tag, TagRepository, TagCreate, TagUpdate]):
    def __init__(self, repository: TagRepository) -> None:
        super().__init__(repository)

    async def get_or_create_by_name(self, name: str) -> Tag:
        existing = await self.repository.get_by_name(name)
        if existing:
            return existing
        return await self.repository.create(Tag(name=name))

    async def get_by_ids(self, ids: list[uuid.UUID]) -> list[Tag]:
        return await self.repository.get_by_ids(ids)

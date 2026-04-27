from typing import Any, Generic, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, id: Any, id_column_name_str: str | None = None) -> ModelType | None:
        col = getattr(self.model, id_column_name_str or "id")
        result = await self.db.execute(select(self.model).where(col == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def create_bulk(self, objs: list[ModelType]) -> list[ModelType]:
        if not objs:
            return []
        self.db.add_all(objs)
        await self.db.flush()
        for obj in objs:
            await self.db.refresh(obj)
        return objs

    async def update(self, obj: ModelType) -> ModelType:
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id: Any, id_column_name_str: str | None = None) -> bool:
        obj = await self.get_by_id(id=id, id_column_name_str=id_column_name_str)
        if obj:
            self.db.delete(obj)
            await self.db.flush()
            return True
        return False

    async def delete_bulk(self, ids: list[Any], id_column_name_str: str | None = None) -> int:
        col = getattr(self.model, id_column_name_str or "id")
        result = await self.db.execute(delete(self.model).where(col.in_(ids)))
        await self.db.flush()
        return result.rowcount

    async def get_by_attributes(self, **filters: Any) -> ModelType | None:
        stmt = select(self.model)
        for attr, value in filters.items():
            if not hasattr(self.model, attr):
                raise AttributeError(f"Model {self.model.__name__} has no attribute '{attr}'")
            col = getattr(self.model, attr)
            stmt = stmt.where(col.in_(value) if isinstance(value, list | set | tuple) else col == value)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_attributes(self, **filters: Any) -> list[ModelType]:
        stmt = select(self.model)
        for attr, value in filters.items():
            if not hasattr(self.model, attr):
                raise AttributeError(f"Model {self.model.__name__} has no attribute '{attr}'")
            col = getattr(self.model, attr)
            stmt = stmt.where(col.in_(value) if isinstance(value, list | set | tuple) else col == value)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

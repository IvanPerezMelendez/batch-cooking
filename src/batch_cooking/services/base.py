from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from ..repositories.base import BaseRepository

ModelType = TypeVar("ModelType")
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)  # type: ignore[type-arg]
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, RepositoryType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, repository: RepositoryType) -> None:
        self.repository = repository

    async def get_by_id(self, id: Any, id_column_name: str | None = None) -> ModelType | None:
        return await self.repository.get_by_id(id, id_column_name)

    async def get_by_id_or_raise(self, id: Any, id_column_name: str | None = None) -> ModelType:
        entity = await self.get_by_id(id, id_column_name)
        if entity is None:
            raise ValueError(f"{self.repository.model.__name__} with id {id} not found")
        return entity

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        return await self.repository.get_all(skip, limit)

    async def get_by_attributes(self, **filters: Any) -> ModelType | None:
        return await self.repository.get_by_attributes(**filters)

    async def get_all_by_attributes(self, **filters: Any) -> list[ModelType]:
        return await self.repository.get_all_by_attributes(**filters)

    async def create(self, create_data: CreateSchemaType) -> ModelType:
        entity = self.repository.model(**create_data.model_dump(exclude_unset=True))
        return await self.repository.create(entity)

    async def get_or_create(self, create_data: CreateSchemaType) -> ModelType:
        model_data = create_data.model_dump(exclude_unset=True)
        entity = await self.repository.get_by_attributes(**model_data)
        if entity:
            return entity
        return await self.repository.create(self.repository.model(**model_data))

    async def create_bulk(self, create_data: list[CreateSchemaType]) -> list[ModelType]:
        if not create_data:
            return []
        entities = [self.repository.model(**d.model_dump(exclude_unset=True)) for d in create_data]
        return await self.repository.create_bulk(entities)

    async def update(self, id: Any, update_data: UpdateSchemaType, id_column_name: str | None = None) -> ModelType:
        entity = await self.get_by_id_or_raise(id, id_column_name)
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(entity, key, value)
        return await self.repository.update(entity)

    async def delete(self, entity_id: Any, id_column_name: str | None = None) -> bool:
        return await self.repository.delete(entity_id, id_column_name)

    async def delete_bulk(self, ids: list[Any], id_column_name: str | None = None) -> int:
        return await self.repository.delete_bulk(ids, id_column_name)

    async def upsert(self, lookup_fields: dict[str, Any], create_data: CreateSchemaType) -> ModelType:
        entities = await self.repository.get_all_by_attributes(**lookup_fields)
        if len(entities) > 1:
            raise ValueError(
                f"Multiple {self.repository.model.__name__} found for {lookup_fields}. Expected at most 1."
            )
        model_data = create_data.model_dump(exclude_unset=True)
        if not entities:
            return await self.repository.create(self.repository.model(**model_data))
        entity = entities[0]
        for key, value in model_data.items():
            setattr(entity, key, value)
        return await self.repository.update(entity)

    async def commit(self) -> None:
        await self.repository.db.commit()

    async def rollback(self) -> None:
        await self.repository.db.rollback()

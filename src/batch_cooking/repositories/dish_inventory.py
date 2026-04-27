import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.dish_inventory import DishInventory
from .base import BaseRepository


class DishInventoryRepository(BaseRepository[DishInventory]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(DishInventory, db)

    async def get_all(self, skip: int = 0, limit: int = 200) -> list[DishInventory]:
        result = await self.db.execute(
            select(DishInventory).order_by(DishInventory.expiry_date).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_recipe(self, recipe_id: uuid.UUID) -> list[DishInventory]:
        result = await self.db.execute(
            select(DishInventory)
            .where(DishInventory.recipe_id == recipe_id)
            .order_by(DishInventory.expiry_date)
        )
        return list(result.scalars().all())

    async def get_available_fifo(self, recipe_id: uuid.UUID) -> list[DishInventory]:
        result = await self.db.execute(
            select(DishInventory)
            .where(DishInventory.recipe_id == recipe_id, DishInventory.servings_remaining > 0)
            .order_by(DishInventory.expiry_date)
        )
        return list(result.scalars().all())

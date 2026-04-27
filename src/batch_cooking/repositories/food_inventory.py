import datetime
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.food_inventory import FoodInventory
from .base import BaseRepository


class FoodInventoryRepository(BaseRepository[FoodInventory]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(FoodInventory, db)

    async def get_all(self, skip: int = 0, limit: int = 200) -> list[FoodInventory]:
        result = await self.db.execute(
            select(FoodInventory)
            .order_by(FoodInventory.expiry_date.asc().nulls_last(), FoodInventory.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_categories(self, q: str = "") -> list[str]:
        stmt = (
            select(func.distinct(FoodInventory.category))
            .where(FoodInventory.category.isnot(None))
            .order_by(FoodInventory.category)
        )
        if q.strip():
            stmt = stmt.where(func.lower(FoodInventory.category).contains(q.lower()))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_expired(self, today: datetime.date) -> list[FoodInventory]:
        result = await self.db.execute(
            select(FoodInventory)
            .where(FoodInventory.expiry_date < today)
            .order_by(FoodInventory.expiry_date)
        )
        return list(result.scalars().all())

    async def deduct_by_ingredient_id(self, ingredient_id: uuid.UUID, quantity: float) -> None:
        result = await self.db.execute(
            select(FoodInventory)
            .where(FoodInventory.ingredient_id == ingredient_id)
            .order_by(FoodInventory.expiry_date.asc().nulls_last())
            .limit(1)
        )
        item = result.scalar_one_or_none()
        if item is None:
            return
        item.quantity -= quantity
        if item.quantity <= 0:
            await self.db.delete(item)
        await self.db.flush()

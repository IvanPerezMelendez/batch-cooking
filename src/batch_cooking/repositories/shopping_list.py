import datetime
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.shopping_list_item import ShoppingListItem
from .base import BaseRepository


class ShoppingListRepository(BaseRepository[ShoppingListItem]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ShoppingListItem, db)

    async def get_all(self, skip: int = 0, limit: int = 500) -> list[ShoppingListItem]:
        result = await self.db.execute(
            select(ShoppingListItem)
            .order_by(ShoppingListItem.category, ShoppingListItem.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending(self) -> list[ShoppingListItem]:
        result = await self.db.execute(
            select(ShoppingListItem)
            .where(ShoppingListItem.is_purchased == False)  # noqa: E712
            .order_by(ShoppingListItem.supermarket, ShoppingListItem.category, ShoppingListItem.name)
        )
        return list(result.scalars().all())

    async def get_unpurchased_by_ingredient(
        self, ingredient_id: uuid.UUID, unit: str | None
    ) -> list[ShoppingListItem]:
        stmt = (
            select(ShoppingListItem)
            .where(
                ShoppingListItem.ingredient_id == ingredient_id,
                ShoppingListItem.is_purchased == False,  # noqa: E712
                ShoppingListItem.quantity.is_not(None),
            )
            .order_by(ShoppingListItem.added_at)
        )
        if unit is not None:
            stmt = stmt.where(ShoppingListItem.unit == unit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_source_date(self, date: datetime.date) -> list[ShoppingListItem]:
        result = await self.db.execute(
            select(ShoppingListItem).where(ShoppingListItem.source_date == date)
        )
        return list(result.scalars().all())

    async def get_all_categories(self, q: str = "") -> list[str]:
        stmt = (
            select(ShoppingListItem.category)
            .where(ShoppingListItem.category.isnot(None))
            .distinct()
            .order_by(ShoppingListItem.category)
        )
        if q.strip():
            stmt = stmt.where(func.lower(ShoppingListItem.category).contains(q.lower()))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_supermarkets(self, q: str = "") -> list[str]:
        stmt = (
            select(ShoppingListItem.supermarket)
            .where(ShoppingListItem.supermarket.isnot(None))
            .distinct()
            .order_by(ShoppingListItem.supermarket)
        )
        if q.strip():
            stmt = stmt.where(func.lower(ShoppingListItem.supermarket).contains(q.lower()))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

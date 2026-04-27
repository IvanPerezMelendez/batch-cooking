import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.meal_slot import MealSlot, MealSlotStatus
from .base import BaseRepository


class MealSlotRepository(BaseRepository[MealSlot]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(MealSlot, db)

    async def get_by_plan(self, plan_id: uuid.UUID) -> list[MealSlot]:
        result = await self.db.execute(
            select(MealSlot)
            .where(MealSlot.plan_id == plan_id)
            .order_by(MealSlot.date, MealSlot.slot_label)
        )
        return list(result.scalars().all())

    async def get_by_date(self, date: datetime.date) -> list[MealSlot]:
        result = await self.db.execute(select(MealSlot).where(MealSlot.date == date))
        return list(result.scalars().all())

    async def get_skipped_with_recipe(self, plan_id: uuid.UUID) -> list[MealSlot]:
        """Pool disponible: slots con receta asignada que no se comieron."""
        result = await self.db.execute(
            select(MealSlot).where(
                MealSlot.plan_id == plan_id,
                MealSlot.status == MealSlotStatus.skipped,
                MealSlot.recipe_id.is_not(None),
            )
        )
        return list(result.scalars().all())

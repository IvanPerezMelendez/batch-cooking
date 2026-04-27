import datetime
import uuid

from ..models.meal_slot import MealSlot, MealSlotStatus
from ..repositories.meal_slot import MealSlotRepository
from .base import BaseService
from .schemas import MealSlotCreate, MealSlotUpdate


class MealSlotService(BaseService[MealSlot, MealSlotRepository, MealSlotCreate, MealSlotUpdate]):
    def __init__(self, repository: MealSlotRepository) -> None:
        super().__init__(repository)

    async def get_by_plan(self, plan_id: uuid.UUID) -> list[MealSlot]:
        return await self.repository.get_by_plan(plan_id)

    async def get_by_date(self, date: datetime.date) -> list[MealSlot]:
        return await self.repository.get_by_date(date)

    async def get_available_pool(self, plan_id: uuid.UUID) -> list[MealSlot]:
        return await self.repository.get_skipped_with_recipe(plan_id)

    async def mark_eaten(self, id: uuid.UUID) -> MealSlot:
        slot = await self.get_by_id_or_raise(id)
        slot.status = MealSlotStatus.eaten
        return await self.repository.update(slot)

    async def mark_skipped(self, id: uuid.UUID) -> MealSlot:
        slot = await self.get_by_id_or_raise(id)
        slot.status = MealSlotStatus.skipped
        return await self.repository.update(slot)

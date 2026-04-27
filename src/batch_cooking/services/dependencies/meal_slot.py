from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...repositories.meal_slot import MealSlotRepository
from ..meal_slot import MealSlotService


def get_meal_slot_service_from_session(session: AsyncSession) -> MealSlotService:
    return MealSlotService(MealSlotRepository(session))


async def get_meal_slot_service(
    session: AsyncSession = Depends(get_db),
) -> MealSlotService:
    return get_meal_slot_service_from_session(session)

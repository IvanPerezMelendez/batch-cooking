from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...repositories.food_inventory import FoodInventoryRepository
from ..food_inventory import FoodInventoryService


def get_food_inventory_service_from_session(session: AsyncSession) -> FoodInventoryService:
    return FoodInventoryService(FoodInventoryRepository(session))


async def get_food_inventory_service(
    session: AsyncSession = Depends(get_db),
) -> FoodInventoryService:
    return get_food_inventory_service_from_session(session)

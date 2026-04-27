from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...repositories.dish_inventory import DishInventoryRepository
from ..dish_inventory import DishInventoryService


def get_dish_inventory_service_from_session(session: AsyncSession) -> DishInventoryService:
    return DishInventoryService(DishInventoryRepository(session))


async def get_dish_inventory_service(
    session: AsyncSession = Depends(get_db),
) -> DishInventoryService:
    return get_dish_inventory_service_from_session(session)

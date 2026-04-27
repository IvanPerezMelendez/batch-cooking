from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...repositories.shopping_list import ShoppingListRepository
from ..shopping_list import ShoppingListService


def get_shopping_list_service_from_session(session: AsyncSession) -> ShoppingListService:
    return ShoppingListService(ShoppingListRepository(session))


async def get_shopping_list_service(
    session: AsyncSession = Depends(get_db),
) -> ShoppingListService:
    return get_shopping_list_service_from_session(session)

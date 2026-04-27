from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...repositories.ingredient import IngredientRepository
from ..ingredient import IngredientService


def get_ingredient_service_from_session(session: AsyncSession) -> IngredientService:
    return IngredientService(IngredientRepository(session))


async def get_ingredient_service(
    session: AsyncSession = Depends(get_db),
) -> IngredientService:
    return get_ingredient_service_from_session(session)

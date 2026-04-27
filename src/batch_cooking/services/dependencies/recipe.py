from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...repositories.recipe import RecipeRepository
from ..recipe import RecipeService


def get_recipe_service_from_session(session: AsyncSession) -> RecipeService:
    return RecipeService(RecipeRepository(session))


async def get_recipe_service(
    session: AsyncSession = Depends(get_db),
) -> RecipeService:
    return get_recipe_service_from_session(session)

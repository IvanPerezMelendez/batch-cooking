from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.ingredient import Ingredient
from .base import BaseRepository


class IngredientRepository(BaseRepository[Ingredient]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Ingredient, db)

    async def get_by_name(self, name: str) -> Ingredient | None:
        result = await self.db.execute(select(Ingredient).where(Ingredient.name == name))
        return result.scalar_one_or_none()

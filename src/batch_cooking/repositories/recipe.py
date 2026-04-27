import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.recipe import Recipe
from ..models.recipe_ingredient import RecipeIngredient
from ..models.recipe_tag import RecipeTag
from .base import BaseRepository


class RecipeRepository(BaseRepository[Recipe]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Recipe, db)

    async def get_by_name(self, name: str) -> Recipe | None:
        result = await self.db.execute(select(Recipe).where(Recipe.name == name))
        return result.scalar_one_or_none()

    async def get_ingredients(self, recipe_id: uuid.UUID) -> list[RecipeIngredient]:
        result = await self.db.execute(
            select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
        )
        return list(result.scalars().all())

    async def replace_ingredients(self, recipe_id: uuid.UUID, items: list[RecipeIngredient]) -> None:
        await self.db.execute(delete(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id))
        self.db.add_all(items)
        await self.db.flush()

    async def get_tags(self, recipe_id: uuid.UUID) -> list[RecipeTag]:
        result = await self.db.execute(
            select(RecipeTag).where(RecipeTag.recipe_id == recipe_id)
        )
        return list(result.scalars().all())

    async def replace_tags(self, recipe_id: uuid.UUID, items: list[RecipeTag]) -> None:
        await self.db.execute(delete(RecipeTag).where(RecipeTag.recipe_id == recipe_id))
        self.db.add_all(items)
        await self.db.flush()

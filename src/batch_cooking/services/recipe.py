import uuid

from ..models.recipe import Recipe
from ..models.recipe_ingredient import RecipeIngredient
from ..models.recipe_tag import RecipeTag
from ..repositories.recipe import RecipeRepository
from .base import BaseService
from .schemas import RecipeCreate, RecipeUpdate


class RecipeService(BaseService[Recipe, RecipeRepository, RecipeCreate, RecipeUpdate]):
    def __init__(self, repository: RecipeRepository) -> None:
        super().__init__(repository)

    async def create(self, create_data: RecipeCreate) -> Recipe:
        recipe = Recipe(
            name=create_data.name,
            servings_produced=create_data.servings_produced,
            days_fridge=create_data.days_fridge,
            days_freezer=create_data.days_freezer,
            notes=create_data.notes,
        )
        recipe = await self.repository.create(recipe)

        if create_data.ingredients:
            items = [
                RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=i.ingredient_id,
                    quantity=i.quantity,
                    unit=i.unit,
                )
                for i in create_data.ingredients
            ]
            await self.repository.replace_ingredients(recipe.id, items)

        if create_data.tag_ids:
            tags = [RecipeTag(recipe_id=recipe.id, tag_id=tid) for tid in create_data.tag_ids]
            await self.repository.replace_tags(recipe.id, tags)

        return recipe

    async def update(self, id: uuid.UUID, update_data: RecipeUpdate, id_column_name: str | None = None) -> Recipe:
        recipe = await self.get_by_id_or_raise(id)

        scalar_fields = update_data.model_dump(exclude_unset=True, exclude={"ingredients", "tag_ids"})
        for key, value in scalar_fields.items():
            setattr(recipe, key, value)
        recipe = await self.repository.update(recipe)

        if update_data.ingredients is not None:
            items = [
                RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=i.ingredient_id,
                    quantity=i.quantity,
                    unit=i.unit,
                )
                for i in update_data.ingredients
            ]
            await self.repository.replace_ingredients(recipe.id, items)

        if update_data.tag_ids is not None:
            tags = [RecipeTag(recipe_id=recipe.id, tag_id=tid) for tid in update_data.tag_ids]
            await self.repository.replace_tags(recipe.id, tags)

        return recipe

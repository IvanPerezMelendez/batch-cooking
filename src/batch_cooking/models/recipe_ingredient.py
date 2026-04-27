import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredient"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipe.id"), primary_key=True
    )
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredient.id"), primary_key=True
    )
    quantity: Mapped[float] = mapped_column(nullable=False)
    unit: Mapped[str] = mapped_column(nullable=False)

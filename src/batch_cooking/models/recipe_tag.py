import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RecipeTag(Base):
    __tablename__ = "recipe_tag"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipe.id"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tag.id"), primary_key=True
    )

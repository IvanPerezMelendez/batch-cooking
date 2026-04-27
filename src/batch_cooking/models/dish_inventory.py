import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class DishLocation(str, enum.Enum):
    fridge = "fridge"
    freezer = "freezer"


class DishInventory(UUIDMixin, Base):
    __tablename__ = "dish_inventory"

    recipe_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("recipe.id"), nullable=True)
    recipe_name_snapshot: Mapped[str] = mapped_column(nullable=False)
    servings_remaining: Mapped[int] = mapped_column(nullable=False)
    location: Mapped[DishLocation] = mapped_column(
        Enum(DishLocation, name="dishlocation"), nullable=False
    )
    cooked_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    expiry_date: Mapped[date] = mapped_column(nullable=False)

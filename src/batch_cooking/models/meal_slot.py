import datetime
import enum
import uuid

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class MealSlotStatus(str, enum.Enum):
    empty = "empty"
    planned = "planned"
    eaten = "eaten"
    skipped = "skipped"


class MealSlot(UUIDMixin, Base):
    __tablename__ = "meal_slot"

    date: Mapped[datetime.date] = mapped_column(nullable=False)
    slot_label: Mapped[str] = mapped_column(nullable=False)
    recipe_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("recipe.id"), nullable=True
    )
    status: Mapped[MealSlotStatus] = mapped_column(
        Enum(MealSlotStatus, name="mealslotstatus"),
        nullable=False,
        default=MealSlotStatus.empty,
    )

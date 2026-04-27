import uuid
from datetime import date, datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class FoodInventory(UUIDMixin, Base):
    __tablename__ = "food_inventory"

    name: Mapped[str] = mapped_column(nullable=False)
    ingredient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ingredient.id"), nullable=True
    )
    quantity: Mapped[float] = mapped_column(nullable=False)
    unit: Mapped[str | None] = mapped_column(nullable=True)
    category: Mapped[str | None] = mapped_column(nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(nullable=True)
    added_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

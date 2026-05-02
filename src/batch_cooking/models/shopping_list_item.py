import datetime
import enum
import uuid

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class ShoppingItemType(str, enum.Enum):
    food = "food"
    dish = "dish"


class ShoppingListItem(UUIDMixin, Base):
    __tablename__ = "shopping_list_item"

    name: Mapped[str] = mapped_column(nullable=False)
    item_type: Mapped[ShoppingItemType] = mapped_column(
        Enum(ShoppingItemType, name="shoppingitemtype"),
        nullable=False,
        default=ShoppingItemType.food,
    )
    ingredient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ingredient.id"), nullable=True
    )
    quantity: Mapped[float | None] = mapped_column(nullable=True)
    unit: Mapped[str | None] = mapped_column(nullable=True)
    category: Mapped[str | None] = mapped_column(nullable=True)
    supermarket: Mapped[str | None] = mapped_column(nullable=True)
    source_date: Mapped[datetime.date | None] = mapped_column(nullable=True)
    is_purchased: Mapped[bool] = mapped_column(nullable=False, default=False)
    added_at: Mapped[datetime.datetime] = mapped_column(nullable=False, default=datetime.datetime.utcnow)

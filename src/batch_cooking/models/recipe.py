from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class Recipe(UUIDMixin, Base):
    __tablename__ = "recipe"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    servings_produced: Mapped[int] = mapped_column(nullable=False)
    days_fridge: Mapped[int] = mapped_column(nullable=False)
    days_freezer: Mapped[int] = mapped_column(nullable=False)
    notes: Mapped[str | None] = mapped_column(nullable=True)

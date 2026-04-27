from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class Ingredient(UUIDMixin, Base):
    __tablename__ = "ingredient"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    default_unit: Mapped[str | None] = mapped_column(nullable=True)
    category: Mapped[str | None] = mapped_column(nullable=True)

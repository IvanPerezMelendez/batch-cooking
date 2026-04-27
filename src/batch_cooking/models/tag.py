from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class Tag(UUIDMixin, Base):
    __tablename__ = "tag"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)

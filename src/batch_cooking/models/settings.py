from typing import Any

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class Settings(UUIDMixin, Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(nullable=False, unique=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=True)

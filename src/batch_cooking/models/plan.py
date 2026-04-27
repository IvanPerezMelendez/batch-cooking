import enum
from datetime import date, datetime

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class PlanStatus(str, enum.Enum):
    draft = "draft"
    confirmed = "confirmed"
    cooked = "cooked"


class Plan(UUIDMixin, Base):
    __tablename__ = "plan"

    week_start: Mapped[date] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, name="planstatus"), nullable=False, default=PlanStatus.draft
    )

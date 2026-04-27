import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.plan import Plan, PlanStatus
from .base import BaseRepository


class PlanRepository(BaseRepository[Plan]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Plan, db)

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Plan]:
        result = await self.db.execute(
            select(Plan).order_by(Plan.week_start.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_week_start(self, week_start: datetime.date) -> Plan | None:
        result = await self.db.execute(select(Plan).where(Plan.week_start == week_start))
        return result.scalar_one_or_none()

    async def get_by_status(self, status: PlanStatus) -> list[Plan]:
        result = await self.db.execute(select(Plan).where(Plan.status == status))
        return list(result.scalars().all())

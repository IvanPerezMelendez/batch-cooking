import datetime
import uuid

from ..models.plan import Plan, PlanStatus
from ..repositories.plan import PlanRepository
from .base import BaseService
from .schemas import PlanCreate, PlanUpdate


class PlanService(BaseService[Plan, PlanRepository, PlanCreate, PlanUpdate]):
    def __init__(self, repository: PlanRepository) -> None:
        super().__init__(repository)

    async def get_by_week_start(self, week_start: datetime.date) -> Plan | None:
        return await self.repository.get_by_week_start(week_start)

    async def get_drafts(self) -> list[Plan]:
        return await self.repository.get_by_status(PlanStatus.draft)

    async def confirm(self, id: uuid.UUID) -> Plan:
        plan = await self.get_by_id_or_raise(id)
        plan.status = PlanStatus.confirmed
        return await self.repository.update(plan)

    async def mark_cooked(self, id: uuid.UUID) -> Plan:
        plan = await self.get_by_id_or_raise(id)
        plan.status = PlanStatus.cooked
        return await self.repository.update(plan)

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...repositories.plan import PlanRepository
from ..plan import PlanService


def get_plan_service_from_session(session: AsyncSession) -> PlanService:
    return PlanService(PlanRepository(session))


async def get_plan_service(
    session: AsyncSession = Depends(get_db),
) -> PlanService:
    return get_plan_service_from_session(session)

import datetime
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.templates import templates
from ...database import get_db
from ...models.meal_slot import MealSlot, MealSlotStatus
from ...models.plan import Plan, PlanStatus
from ...repositories.meal_slot import MealSlotRepository
from ...repositories.plan import PlanRepository
from ...repositories.recipe import RecipeRepository
from ...services.dependencies.dish_inventory import get_dish_inventory_service_from_session
from ...services.dependencies.recipe import get_recipe_service
from ...services.dependencies.settings import get_settings_service
from ...services.recipe import RecipeService
from ...services.settings import SettingsService

router = APIRouter(prefix="/week", tags=["week"])

DAYS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
DEFAULT_SLOTS = ["Comida", "Cena"]
_TODAY = datetime.date.today


def _week_start(today: datetime.date) -> datetime.date:
    return today - datetime.timedelta(days=today.weekday())


def _ctx(**kwargs):
    return {"today": _TODAY(), **kwargs}


async def _build_days(slots: list[MealSlot], week_start: datetime.date) -> list[dict]:
    slots_by_date: dict[datetime.date, list[MealSlot]] = defaultdict(list)
    for s in slots:
        slots_by_date[s.date].append(s)
    days = []
    for i in range(7):
        d = week_start + datetime.timedelta(days=i)
        days.append({"date": d, "label": DAYS_ES[i], "slots": slots_by_date.get(d, [])})
    return days


async def _load_recipe_map(db: AsyncSession, slots: list[MealSlot]) -> dict:
    recipe_ids = {s.recipe_id for s in slots if s.recipe_id}
    if not recipe_ids:
        return {}
    repo = RecipeRepository(db)
    recipe_map = {}
    for rid in recipe_ids:
        r = await repo.get_by_id(rid)
        if r:
            recipe_map[r.id] = r
    return recipe_map


# ── Página principal ──────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def get_week(
    request: Request,
    db: AsyncSession = Depends(get_db),
    recipe_svc: RecipeService = Depends(get_recipe_service),
    settings_svc: SettingsService = Depends(get_settings_service),
):
    plan_repo = PlanRepository(db)
    slot_repo = MealSlotRepository(db)

    today = _TODAY()
    ws = _week_start(today)
    plan = await plan_repo.get_by_week_start(ws)

    if plan is None:
        plan = await plan_repo.create(Plan(week_start=ws, status=PlanStatus.draft))
        slot_labels = await settings_svc.get("default_meal_slots") or DEFAULT_SLOTS
        slot_objs = [
            MealSlot(plan_id=plan.id, date=ws + datetime.timedelta(days=d), slot_label=label)
            for d in range(7)
            for label in slot_labels
        ]
        db.add_all(slot_objs)
        await db.flush()
        await db.commit()
        await db.refresh(plan)

    slots = await slot_repo.get_by_plan(plan.id)
    recipe_by_id = await _load_recipe_map(db, slots)
    days = await _build_days(slots, ws)
    skipped = [s for s in slots if s.status == MealSlotStatus.skipped and s.recipe_id]
    week_end = ws + datetime.timedelta(days=6)

    return templates.TemplateResponse(
        request, "week.html",
        _ctx(plan=plan, days=days, recipe_by_id=recipe_by_id, skipped=skipped, week_end=week_end),
    )


# ── Acciones de slot ──────────────────────────────────────────────────────────

async def _slot_response(slot_id: uuid.UUID, db: AsyncSession, request: Request):
    slot_repo = MealSlotRepository(db)
    slot = await slot_repo.get_by_id(slot_id)
    if slot is None:
        return None, None
    recipe_by_id = await _load_recipe_map(db, [slot])
    return slot, recipe_by_id


@router.post("/slots/{slot_id}/eat", response_class=HTMLResponse)
async def mark_eaten(
    slot_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    slot_repo = MealSlotRepository(db)
    slot = await slot_repo.get_by_id(slot_id)
    if slot is None:
        return Response(status_code=404)

    if slot.status != MealSlotStatus.eaten:
        if slot.recipe_id is not None:
            dish_svc = get_dish_inventory_service_from_session(db)
            await dish_svc.consume_serving(slot.recipe_id)
        slot.status = MealSlotStatus.eaten
        await db.flush()
        await db.commit()
        await db.refresh(slot)

    recipe_by_id = await _load_recipe_map(db, [slot])
    return templates.TemplateResponse(
        request, "partials/week_slot.html",
        _ctx(slot=slot, recipe_by_id=recipe_by_id),
    )


@router.post("/slots/{slot_id}/skip", response_class=HTMLResponse)
async def mark_skipped(
    slot_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    slot_repo = MealSlotRepository(db)
    slot = await slot_repo.get_by_id(slot_id)
    if slot is None:
        return Response(status_code=404)

    slot.status = MealSlotStatus.skipped
    await db.flush()
    await db.commit()
    await db.refresh(slot)

    recipe_by_id = await _load_recipe_map(db, [slot])
    return templates.TemplateResponse(
        request, "partials/week_slot.html",
        _ctx(slot=slot, recipe_by_id=recipe_by_id),
    )


@router.post("/slots/{slot_id}/reset", response_class=HTMLResponse)
async def reset_slot(
    slot_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    slot_repo = MealSlotRepository(db)
    slot = await slot_repo.get_by_id(slot_id)
    if slot is None:
        return Response(status_code=404)

    slot.status = MealSlotStatus.empty
    await db.flush()
    await db.commit()
    await db.refresh(slot)

    recipe_by_id = await _load_recipe_map(db, [slot])
    return templates.TemplateResponse(
        request, "partials/week_slot.html",
        _ctx(slot=slot, recipe_by_id=recipe_by_id),
    )

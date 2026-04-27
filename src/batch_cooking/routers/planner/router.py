import datetime
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.templates import templates
from ...database import get_db
from ...models.plan import Plan, PlanStatus
from ...models.meal_slot import MealSlot
from ...repositories.ingredient import IngredientRepository
from ...repositories.meal_slot import MealSlotRepository
from ...repositories.plan import PlanRepository
from ...repositories.recipe import RecipeRepository
from ...repositories.shopping_list import ShoppingListRepository
from ...services.dependencies.meal_slot import get_meal_slot_service
from ...services.dependencies.plan import get_plan_service
from ...services.dependencies.recipe import get_recipe_service
from ...services.dependencies.settings import get_settings_service
from ...services.meal_slot import MealSlotService
from ...services.plan import PlanService
from ...services.recipe import RecipeService
from ...services.settings import SettingsService
from ...services.schemas import MealSlotCreate, PlanCreate, ShoppingListItemCreate
from ...models.shopping_list_item import ShoppingItemType

router = APIRouter(prefix="/planner", tags=["planner"])

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


# ── Página principal ──────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def get_planner(
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
            MealSlot(
                plan_id=plan.id,
                date=ws + datetime.timedelta(days=d),
                slot_label=label,
            )
            for d in range(7)
            for label in slot_labels
        ]
        db.add_all(slot_objs)
        await db.flush()
        await db.commit()
        await db.refresh(plan)

    slots = await slot_repo.get_by_plan(plan.id)
    recipes = await recipe_svc.get_all(limit=500)
    recipe_by_id = {r.id: r for r in recipes}
    days = await _build_days(slots, ws)

    return templates.TemplateResponse(
        request, "planner.html",
        _ctx(plan=plan, days=days, recipe_by_id=recipe_by_id, recipes=recipes),
    )


# ── Modal para asignar receta ─────────────────────────────────────────────────

@router.get("/slots/{slot_id}/assign-modal", response_class=HTMLResponse)
async def assign_modal(
    slot_id: uuid.UUID,
    request: Request,
    recipe_svc: RecipeService = Depends(get_recipe_service),
):
    recipes = await recipe_svc.get_all(limit=500)
    return templates.TemplateResponse(
        request, "partials/planner_assign_modal.html",
        _ctx(slot_id=slot_id, recipes=recipes),
    )


# ── Asignar receta a un slot ──────────────────────────────────────────────────

@router.patch("/slots/{slot_id}", response_class=HTMLResponse)
async def assign_recipe(
    slot_id: uuid.UUID,
    request: Request,
    recipe_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    plan_svc: PlanService = Depends(get_plan_service),
    recipe_svc: RecipeService = Depends(get_recipe_service),
):
    slot_repo = MealSlotRepository(db)
    slot = await slot_repo.get_by_id(slot_id)
    if slot is None:
        return Response(status_code=404)

    rid = uuid.UUID(recipe_id) if recipe_id.strip() else None
    slot.recipe_id = rid
    await db.flush()
    await db.commit()
    await db.refresh(slot)

    plan = await plan_svc.get_by_id_or_raise(slot.plan_id)
    recipe_by_id = {}
    if rid:
        recipe = await recipe_svc.get_by_id(rid)
        if recipe:
            recipe_by_id[recipe.id] = recipe

    return templates.TemplateResponse(
        request, "partials/planner_slot.html",
        _ctx(slot=slot, plan=plan, recipe_by_id=recipe_by_id),
    )


# ── Desasignar receta de un slot ──────────────────────────────────────────────

@router.delete("/slots/{slot_id}/recipe", response_class=HTMLResponse)
async def unassign_recipe(
    slot_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    plan_svc: PlanService = Depends(get_plan_service),
):
    slot_repo = MealSlotRepository(db)
    slot = await slot_repo.get_by_id(slot_id)
    if slot is None:
        return Response(status_code=404)

    slot.recipe_id = None
    await db.flush()
    await db.commit()
    await db.refresh(slot)

    plan = await plan_svc.get_by_id_or_raise(slot.plan_id)
    return templates.TemplateResponse(
        request, "partials/planner_slot.html",
        _ctx(slot=slot, plan=plan, recipe_by_id={}),
    )


# ── Confirmar plan → vuelca ingredientes a la lista de la compra ──────────────

@router.post("/{plan_id}/confirm")
async def confirm_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    plan_svc: PlanService = Depends(get_plan_service),
):
    plan = await plan_svc.get_by_id_or_raise(plan_id)
    if plan.status != PlanStatus.draft:
        resp = Response(status_code=409)
        return resp

    slot_repo = MealSlotRepository(db)
    recipe_repo = RecipeRepository(db)
    ingredient_repo = IngredientRepository(db)
    sl_repo = ShoppingListRepository(db)

    slots = await slot_repo.get_by_plan(plan_id)
    seen_recipe_ids: set[uuid.UUID] = set()
    shopping_items = []

    for slot in slots:
        if slot.recipe_id is None or slot.recipe_id in seen_recipe_ids:
            continue
        seen_recipe_ids.add(slot.recipe_id)

        recipe_ingredients = await recipe_repo.get_ingredients(slot.recipe_id)
        for ri in recipe_ingredients:
            ingredient = await ingredient_repo.get_by_id(ri.ingredient_id)
            if ingredient is None:
                continue
            from ...models.shopping_list_item import ShoppingListItem
            shopping_items.append(ShoppingListItem(
                name=ingredient.name,
                item_type=ShoppingItemType.food,
                ingredient_id=ingredient.id,
                quantity=ri.quantity,
                unit=ri.unit,
                category=ingredient.category,
                source_plan_id=plan_id,
            ))

    if shopping_items:
        db.add_all(shopping_items)
        await db.flush()

    plan.status = PlanStatus.confirmed
    await db.flush()
    await db.commit()

    resp = Response(status_code=200)
    resp.headers["HX-Redirect"] = "/shopping-list"
    return resp

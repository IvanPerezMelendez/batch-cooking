import datetime
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.templates import templates
from ...database import get_db
from ...models.meal_slot import MealSlot, MealSlotStatus
from ...models.shopping_list_item import ShoppingListItem, ShoppingItemType
from ...repositories.ingredient import IngredientRepository
from ...repositories.meal_slot import MealSlotRepository
from ...repositories.recipe import RecipeRepository
from ...repositories.shopping_list import ShoppingListRepository
from ...services.dependencies.recipe import get_recipe_service
from ...services.dependencies.settings import get_settings_service
from ...services.recipe import RecipeService
from ...services.settings import SettingsService

router = APIRouter(prefix="/planner", tags=["planner"])

DAYS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
DEFAULT_SLOTS = ["Comida", "Cena"]
_TODAY = datetime.date.today

BACK_DAYS = 2
DEFAULT_WINDOW = 15


def _ctx(**kwargs):
    return {"today": _TODAY(), **kwargs}


# ── Página principal ──────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def get_planner(
    request: Request,
    window: int = Query(default=DEFAULT_WINDOW, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    recipe_svc: RecipeService = Depends(get_recipe_service),
    settings_svc: SettingsService = Depends(get_settings_service),
):
    slot_repo = MealSlotRepository(db)

    today = _TODAY()
    start_date = today - datetime.timedelta(days=BACK_DAYS)
    end_date = today + datetime.timedelta(days=window)
    total_days = (end_date - start_date).days + 1

    # Ensure slots exist for every day in the visible range
    slot_labels: list[str] | None = None
    for i in range(total_days):
        d = start_date + datetime.timedelta(days=i)
        if not await slot_repo.get_by_date(d):
            if slot_labels is None:
                slot_labels = await settings_svc.get("default_meal_slots") or DEFAULT_SLOTS
            db.add_all([MealSlot(date=d, slot_label=lbl) for lbl in slot_labels])
    await db.commit()

    slots = await slot_repo.get_by_date_range(start_date, end_date)
    slots_by_date: dict[datetime.date, list[MealSlot]] = defaultdict(list)
    for s in slots:
        slots_by_date[s.date].append(s)

    recipes = await recipe_svc.get_all(limit=500)
    recipe_by_id = {r.id: r for r in recipes}

    days = [
        {
            "date": start_date + datetime.timedelta(days=i),
            "label": DAYS_ES[(start_date + datetime.timedelta(days=i)).weekday()],
            "slots": slots_by_date.get(start_date + datetime.timedelta(days=i), []),
            "is_today": (start_date + datetime.timedelta(days=i)) == today,
            "is_past": (start_date + datetime.timedelta(days=i)) < today,
        }
        for i in range(total_days)
    ]

    return templates.TemplateResponse(
        request, "planner.html",
        _ctx(
            days=days,
            recipes=recipes,
            recipe_by_id=recipe_by_id,
            window=window,
            start_date=start_date,
            end_date=end_date,
        ),
    )


# ── Limpiar todas las recetas de un día ──────────────────────────────────────

@router.delete("/day/{date_str}", response_class=HTMLResponse)
async def clear_day(
    date_str: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        date = datetime.date.fromisoformat(date_str)
    except ValueError:
        return Response(status_code=422)

    slot_repo = MealSlotRepository(db)
    for slot in await slot_repo.get_by_date(date):
        slot.recipe_id = None
        slot.status = MealSlotStatus.empty
    await db.commit()

    today = _TODAY()
    day = {
        "date": date,
        "label": DAYS_ES[date.weekday()],
        "slots": await slot_repo.get_by_date(date),
        "is_today": date == today,
        "is_past": date < today,
    }
    return templates.TemplateResponse(
        request, "partials/planner_day.html",
        _ctx(day=day, recipe_by_id={}),
    )


# ── Añadir rango a la lista de la compra ─────────────────────────────────────

@router.post("/add-to-shopping")
async def add_to_shopping(
    start: datetime.date = Form(...),
    end: datetime.date = Form(...),
    db: AsyncSession = Depends(get_db),
):
    from collections import Counter

    slot_repo = MealSlotRepository(db)
    recipe_repo = RecipeRepository(db)
    ingredient_repo = IngredientRepository(db)

    slots = await slot_repo.get_by_date_range(start, end)

    # How many slots each recipe is assigned to (each slot = 1 serving)
    recipe_slot_counts: Counter[uuid.UUID] = Counter(
        slot.recipe_id for slot in slots if slot.recipe_id
    )

    # Aggregate by (ingredient_id, unit) to merge identical ingredients
    # across recipes or repeated recipe assignments
    aggregated: dict[tuple, dict] = {}

    for recipe_id, slot_count in recipe_slot_counts.items():
        recipe = await recipe_repo.get_by_id(recipe_id)
        if recipe is None:
            continue
        servings = recipe.servings_produced or 1

        for ri in await recipe_repo.get_ingredients(recipe_id):
            ingredient = await ingredient_repo.get_by_id(ri.ingredient_id)
            if ingredient is None:
                continue

            # quantity per slot = full recipe quantity / servings_produced
            per_slot = (ri.quantity / servings) if ri.quantity is not None else None
            total = (per_slot * slot_count) if per_slot is not None else None

            key = (ingredient.id, ri.unit)
            if key in aggregated:
                existing_qty = aggregated[key]["quantity"]
                if total is not None and existing_qty is not None:
                    aggregated[key]["quantity"] = existing_qty + total
                # if either side is None we leave it as-is
            else:
                aggregated[key] = {
                    "name": ingredient.name,
                    "ingredient_id": ingredient.id,
                    "quantity": total,
                    "unit": ri.unit,
                    "category": ingredient.category,
                }

    items = [
        ShoppingListItem(
            name=v["name"],
            item_type=ShoppingItemType.food,
            ingredient_id=v["ingredient_id"],
            quantity=v["quantity"],
            unit=v["unit"],
            category=v["category"],
            source_date=start,
        )
        for v in aggregated.values()
    ]

    if items:
        db.add_all(items)
        await db.commit()

    resp = Response(status_code=200)
    resp.headers["HX-Redirect"] = "/shopping-list"
    return resp


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
    recipe_svc: RecipeService = Depends(get_recipe_service),
):
    slot_repo = MealSlotRepository(db)
    slot = await slot_repo.get_by_id(slot_id)
    if slot is None:
        return Response(status_code=404)

    rid = uuid.UUID(recipe_id) if recipe_id.strip() else None
    slot.recipe_id = rid
    await db.commit()
    await db.refresh(slot)

    recipe_by_id = {}
    if rid:
        recipe = await recipe_svc.get_by_id(rid)
        if recipe:
            recipe_by_id[recipe.id] = recipe

    return templates.TemplateResponse(
        request, "partials/planner_slot.html",
        _ctx(slot=slot, recipe_by_id=recipe_by_id),
    )


# ── Desasignar receta de un slot ──────────────────────────────────────────────

@router.delete("/slots/{slot_id}/recipe", response_class=HTMLResponse)
async def unassign_recipe(
    slot_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    slot_repo = MealSlotRepository(db)
    slot = await slot_repo.get_by_id(slot_id)
    if slot is None:
        return Response(status_code=404)

    old_recipe_id = slot.recipe_id
    slot.recipe_id = None
    slot.status = MealSlotStatus.empty
    await db.commit()
    await db.refresh(slot)

    # Subtract the per-serving quantities from the shopping list
    if old_recipe_id is not None:
        recipe_repo = RecipeRepository(db)
        ingredient_repo = IngredientRepository(db)
        sl_repo = ShoppingListRepository(db)

        recipe = await recipe_repo.get_by_id(old_recipe_id)
        if recipe:
            servings = recipe.servings_produced or 1
            for ri in await recipe_repo.get_ingredients(old_recipe_id):
                if ri.quantity is None:
                    continue
                per_slot = ri.quantity / servings
                to_subtract = per_slot
                for item in await sl_repo.get_unpurchased_by_ingredient(ri.ingredient_id, ri.unit):
                    if to_subtract <= 0:
                        break
                    if item.quantity <= to_subtract:
                        to_subtract -= item.quantity
                        await db.delete(item)
                    else:
                        item.quantity = round(item.quantity - to_subtract, 6)
                        to_subtract = 0
            await db.commit()

    return templates.TemplateResponse(
        request, "partials/planner_slot.html",
        _ctx(slot=slot, recipe_by_id={}),
    )

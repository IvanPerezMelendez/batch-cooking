import datetime
import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.templates import templates
from ...database import get_db
from ...models.dish_inventory import DishInventory, DishLocation
from ...repositories.meal_slot import MealSlotRepository
from ...repositories.recipe import RecipeRepository
from ...services.dependencies.food_inventory import get_food_inventory_service
from ...services.dependencies.recipe import get_recipe_service
from ...services.food_inventory import FoodInventoryService
from ...services.recipe import RecipeService

router = APIRouter(prefix="/cooking", tags=["cooking"])

_TODAY = datetime.date.today
COOKING_HORIZON_DAYS = 14


def _ctx(**kwargs):
    return {"today": _TODAY(), **kwargs}


# ── Página principal ──────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def get_cooking(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    slot_repo = MealSlotRepository(db)
    recipe_repo = RecipeRepository(db)

    today = _TODAY()
    end = today + datetime.timedelta(days=COOKING_HORIZON_DAYS)
    slots = await slot_repo.get_by_date_range(today, end)

    seen: set[uuid.UUID] = set()
    recipes = []
    for slot in slots:
        if slot.recipe_id and slot.recipe_id not in seen:
            seen.add(slot.recipe_id)
            r = await recipe_repo.get_by_id(slot.recipe_id)
            if r:
                recipes.append(r)

    return templates.TemplateResponse(
        request, "cooking.html",
        _ctx(recipes=recipes),
    )


# ── Modal para confirmar cocción ──────────────────────────────────────────────

@router.get("/{recipe_id}/cook-modal", response_class=HTMLResponse)
async def cook_modal(
    recipe_id: uuid.UUID,
    request: Request,
    recipe_svc: RecipeService = Depends(get_recipe_service),
):
    recipe = await recipe_svc.get_by_id_or_raise(recipe_id)
    return templates.TemplateResponse(
        request, "partials/cooking_cook_modal.html",
        _ctx(recipe=recipe),
    )


# ── Registrar cocción ──────────────────────────────────────────────────────────

@router.post("/{recipe_id}/cook", response_class=HTMLResponse)
async def cook_recipe(
    recipe_id: uuid.UUID,
    request: Request,
    servings_obtained: int = Form(...),
    location: DishLocation = Form(...),
    db: AsyncSession = Depends(get_db),
    recipe_svc: RecipeService = Depends(get_recipe_service),
    food_svc: FoodInventoryService = Depends(get_food_inventory_service),
):
    recipe = await recipe_svc.get_by_id_or_raise(recipe_id)

    days = recipe.days_fridge if location == DishLocation.fridge else recipe.days_freezer
    expiry_date = _TODAY() + datetime.timedelta(days=days)

    dish = DishInventory(
        recipe_id=recipe_id,
        recipe_name_snapshot=recipe.name,
        servings_remaining=servings_obtained,
        location=location,
        expiry_date=expiry_date,
    )
    db.add(dish)
    await db.flush()

    recipe_repo = RecipeRepository(db)
    recipe_ingredients = await recipe_repo.get_ingredients(recipe_id)
    for ri in recipe_ingredients:
        await food_svc.deduct_by_ingredient_id(ri.ingredient_id, ri.quantity)

    await db.commit()
    await food_svc.commit()

    return templates.TemplateResponse(
        request, "partials/cooking_recipe_row.html",
        _ctx(recipe=recipe, cooked=True,
             servings_obtained=servings_obtained, location=location),
    )

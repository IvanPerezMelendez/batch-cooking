import datetime
import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.templates import templates
from ...database import get_db
from ...models.dish_inventory import DishInventory, DishLocation
from ...models.plan import PlanStatus
from ...repositories.meal_slot import MealSlotRepository
from ...repositories.plan import PlanRepository
from ...repositories.recipe import RecipeRepository
from ...services.dependencies.food_inventory import get_food_inventory_service
from ...services.dependencies.plan import get_plan_service
from ...services.dependencies.recipe import get_recipe_service
from ...services.food_inventory import FoodInventoryService
from ...services.plan import PlanService
from ...services.recipe import RecipeService

router = APIRouter(prefix="/cooking", tags=["cooking"])

_TODAY = datetime.date.today


def _ctx(**kwargs):
    return {"today": _TODAY(), **kwargs}


# ── Página principal ──────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def get_cooking(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    plan_repo = PlanRepository(db)
    slot_repo = MealSlotRepository(db)
    recipe_repo = RecipeRepository(db)

    confirmed_plans = await plan_repo.get_by_status(PlanStatus.confirmed)

    plan_data = []
    for plan in confirmed_plans:
        slots = await slot_repo.get_by_plan(plan.id)
        seen: set[uuid.UUID] = set()
        recipes = []
        for slot in slots:
            if slot.recipe_id and slot.recipe_id not in seen:
                seen.add(slot.recipe_id)
                recipe = await recipe_repo.get_by_id(slot.recipe_id)
                if recipe:
                    recipes.append(recipe)
        plan_data.append({"plan": plan, "recipes": recipes})

    return templates.TemplateResponse(
        request, "cooking.html",
        _ctx(plan_data=plan_data),
    )


# ── Modal para confirmar cocción ──────────────────────────────────────────────

@router.get("/{plan_id}/{recipe_id}/cook-modal", response_class=HTMLResponse)
async def cook_modal(
    plan_id: uuid.UUID,
    recipe_id: uuid.UUID,
    request: Request,
    recipe_svc: RecipeService = Depends(get_recipe_service),
):
    recipe = await recipe_svc.get_by_id_or_raise(recipe_id)
    return templates.TemplateResponse(
        request, "partials/cooking_cook_modal.html",
        _ctx(plan_id=plan_id, recipe=recipe),
    )


# ── Registrar cocción ──────────────────────────────────────────────────────────

@router.post("/{plan_id}/{recipe_id}/cook", response_class=HTMLResponse)
async def cook_recipe(
    plan_id: uuid.UUID,
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
        _ctx(plan_id=plan_id, recipe=recipe, cooked=True,
             servings_obtained=servings_obtained, location=location),
    )


# ── Marcar plan como cocinado ─────────────────────────────────────────────────

@router.post("/{plan_id}/mark-done")
async def mark_plan_done(
    plan_id: uuid.UUID,
    plan_svc: PlanService = Depends(get_plan_service),
):
    await plan_svc.mark_cooked(plan_id)
    await plan_svc.commit()
    resp = Response(status_code=200)
    resp.headers["HX-Redirect"] = "/cooking"
    return resp

import datetime
import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response

from ...core.templates import templates
from ...services.dependencies.dish_inventory import get_dish_inventory_service
from ...services.dependencies.food_inventory import get_food_inventory_service
from ...services.dish_inventory import DishInventoryService
from ...services.food_inventory import FoodInventoryService
from ...models.dish_inventory import DishLocation
from ...services.schemas import DishInventoryCreate, FoodInventoryCreate, FoodInventoryUpdate

router = APIRouter(prefix="/inventory", tags=["inventory"])

_TODAY = datetime.date.today


# ── helpers ──────────────────────────────────────────────────────────────────

def _ctx(**kwargs):
    return {"today": _TODAY(), **kwargs}


# ── Autocomplete categorías ───────────────────────────────────────────────────

@router.get("/autocomplete/categories", response_class=HTMLResponse)
async def autocomplete_inv_categories(
    request: Request,
    q: str = "",
    svc: FoodInventoryService = Depends(get_food_inventory_service),
):
    options = await svc.get_all_categories(q)
    return templates.TemplateResponse(
        request, "partials/autocomplete_options.html", {"options": options},
    )


# ── Alimentos: página principal ───────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def get_inventory(
    request: Request,
    svc: FoodInventoryService = Depends(get_food_inventory_service),
):
    food_items = await svc.get_all()
    return templates.TemplateResponse(
        request, "inventory.html",
        _ctx(food_items=food_items, active_tab="food"),
    )


@router.post("/food", response_class=HTMLResponse)
async def add_food_item(
    request: Request,
    name: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form(""),
    category: str = Form(""),
    expiry_date: str = Form(""),
    svc: FoodInventoryService = Depends(get_food_inventory_service),
):
    data = FoodInventoryCreate(
        name=name.strip(),
        quantity=quantity,
        unit=unit.strip() or None,
        category=category.strip() or None,
        expiry_date=datetime.date.fromisoformat(expiry_date) if expiry_date else None,
    )
    item = await svc.create(data)
    await svc.commit()
    return templates.TemplateResponse(
        request, "partials/food_item_row.html", _ctx(item=item),
    )


@router.get("/food/{item_id}", response_class=HTMLResponse)
async def get_food_item_row(
    item_id: uuid.UUID,
    request: Request,
    svc: FoodInventoryService = Depends(get_food_inventory_service),
):
    item = await svc.get_by_id_or_raise(item_id)
    return templates.TemplateResponse(
        request, "partials/food_item_row.html", _ctx(item=item),
    )


@router.get("/food/{item_id}/edit", response_class=HTMLResponse)
async def edit_food_item_form(
    item_id: uuid.UUID,
    request: Request,
    svc: FoodInventoryService = Depends(get_food_inventory_service),
):
    item = await svc.get_by_id_or_raise(item_id)
    return templates.TemplateResponse(
        request, "partials/food_item_edit_form.html", _ctx(item=item),
    )


@router.patch("/food/{item_id}", response_class=HTMLResponse)
async def update_food_item(
    item_id: uuid.UUID,
    request: Request,
    name: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form(""),
    category: str = Form(""),
    expiry_date: str = Form(""),
    svc: FoodInventoryService = Depends(get_food_inventory_service),
):
    data = FoodInventoryUpdate(
        name=name.strip(),
        quantity=quantity,
        unit=unit.strip() or None,
        category=category.strip() or None,
        expiry_date=datetime.date.fromisoformat(expiry_date) if expiry_date else None,
    )
    item = await svc.update(item_id, data)
    await svc.commit()
    return templates.TemplateResponse(
        request, "partials/food_item_row.html", _ctx(item=item),
    )


@router.delete("/food/{item_id}")
async def delete_food_item(
    item_id: uuid.UUID,
    svc: FoodInventoryService = Depends(get_food_inventory_service),
):
    await svc.delete(item_id)
    await svc.commit()
    return Response(status_code=200)


# ── Platos ────────────────────────────────────────────────────────────────────

@router.get("/dishes", response_class=HTMLResponse)
async def get_dishes(
    request: Request,
    svc: DishInventoryService = Depends(get_dish_inventory_service),
):
    dish_items = await svc.get_all()
    return templates.TemplateResponse(
        request, "inventory.html",
        _ctx(dish_items=dish_items, active_tab="dishes"),
    )


@router.get("/modal/food", response_class=HTMLResponse)
async def modal_food_form(
    request: Request,
    svc: FoodInventoryService = Depends(get_food_inventory_service),
):
    categories = await svc.get_all_categories()
    return templates.TemplateResponse(request, "partials/modal_food_form.html", _ctx(categories=categories))


@router.get("/modal/dish", response_class=HTMLResponse)
async def modal_dish_form(request: Request):
    return templates.TemplateResponse(request, "partials/modal_dish_form.html", _ctx())


@router.post("/dish", response_class=HTMLResponse)
async def add_dish_item(
    request: Request,
    recipe_name_snapshot: str = Form(...),
    servings_remaining: int = Form(...),
    location: DishLocation = Form(...),
    expiry_date: str = Form(...),
    svc: DishInventoryService = Depends(get_dish_inventory_service),
):
    data = DishInventoryCreate(
        recipe_name_snapshot=recipe_name_snapshot.strip(),
        servings_remaining=servings_remaining,
        location=location,
        expiry_date=datetime.date.fromisoformat(expiry_date),
    )
    item = await svc.create(data)
    await svc.commit()
    return templates.TemplateResponse(
        request, "partials/dish_item_row.html", _ctx(item=item),
    )


@router.delete("/dish/{item_id}")
async def delete_dish_item(
    item_id: uuid.UUID,
    svc: DishInventoryService = Depends(get_dish_inventory_service),
):
    await svc.delete(item_id)
    await svc.commit()
    return Response(status_code=200)

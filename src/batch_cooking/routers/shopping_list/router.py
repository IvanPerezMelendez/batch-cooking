import datetime
import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response

from ...core.templates import templates
from ...models.dish_inventory import DishLocation
from ...models.shopping_list_item import ShoppingItemType
from ...services.dependencies.dish_inventory import get_dish_inventory_service
from ...services.dependencies.food_inventory import get_food_inventory_service
from ...services.dependencies.shopping_list import get_shopping_list_service
from ...services.dish_inventory import DishInventoryService
from ...services.food_inventory import FoodInventoryService
from ...services.schemas import (
    DishInventoryCreate,
    FoodInventoryCreate,
    ShoppingListItemCreate,
)
from ...services.shopping_list import ShoppingListService

router = APIRouter(prefix="/shopping-list", tags=["shopping-list"])

_TODAY = datetime.date.today


def _ctx(**kwargs):
    return {"today": _TODAY(), **kwargs}


# ── Autocomplete ──────────────────────────────────────────────────────────────

@router.get("/autocomplete/categories", response_class=HTMLResponse)
async def autocomplete_categories(
    request: Request,
    q: str = "",
    svc: ShoppingListService = Depends(get_shopping_list_service),
):
    options = await svc.get_all_categories(q)
    return templates.TemplateResponse(
        request, "partials/autocomplete_options.html", {"options": options},
    )


@router.get("/autocomplete/supermarkets", response_class=HTMLResponse)
async def autocomplete_supermarkets(
    request: Request,
    q: str = "",
    svc: ShoppingListService = Depends(get_shopping_list_service),
):
    options = await svc.get_all_supermarkets(q)
    return templates.TemplateResponse(
        request, "partials/autocomplete_options.html", {"options": options},
    )


# ── Modal ─────────────────────────────────────────────────────────────────────

@router.get("/modal", response_class=HTMLResponse)
async def modal_shopping_form(request: Request):
    return templates.TemplateResponse(request, "partials/modal_shopping_form.html", _ctx())


# ── Página principal ──────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def get_shopping_list(
    request: Request,
    svc: ShoppingListService = Depends(get_shopping_list_service),
):
    items = await svc.get_pending()
    categories = await svc.get_all_categories()
    supermarkets = await svc.get_all_supermarkets()
    return templates.TemplateResponse(
        request, "shopping_list.html",
        _ctx(items=items, categories=categories, supermarkets=supermarkets),
    )


# ── Añadir ítem ───────────────────────────────────────────────────────────────

@router.post("", response_class=HTMLResponse)
async def add_shopping_item(
    request: Request,
    name: str = Form(...),
    item_type: ShoppingItemType = Form(ShoppingItemType.food),
    quantity: str = Form(""),
    unit: str = Form(""),
    category: str = Form(""),
    supermarket: str = Form(""),
    svc: ShoppingListService = Depends(get_shopping_list_service),
):
    data = ShoppingListItemCreate(
        name=name.strip(),
        item_type=item_type,
        quantity=float(quantity) if quantity.strip() else None,
        unit=unit.strip() or None,
        category=category.strip() or None,
        supermarket=supermarket.strip() or None,
    )
    item = await svc.create(data)
    await svc.commit()
    return templates.TemplateResponse(
        request, "partials/shopping_item_row.html", _ctx(item=item),
    )


# ── Eliminar ítem ─────────────────────────────────────────────────────────────

@router.delete("/{item_id}")
async def delete_shopping_item(
    item_id: uuid.UUID,
    svc: ShoppingListService = Depends(get_shopping_list_service),
):
    await svc.delete(item_id)
    await svc.commit()
    return Response(status_code=200)


# ── Formulario "comprado" (inline expand) ─────────────────────────────────────

@router.get("/{item_id}/bought-form", response_class=HTMLResponse)
async def bought_form(
    item_id: uuid.UUID,
    request: Request,
    svc: ShoppingListService = Depends(get_shopping_list_service),
):
    item = await svc.get_by_id_or_raise(item_id)
    return templates.TemplateResponse(
        request, "partials/shopping_item_bought_form.html", _ctx(item=item),
    )


@router.get("/{item_id}/row", response_class=HTMLResponse)
async def get_shopping_item_row(
    item_id: uuid.UUID,
    request: Request,
    svc: ShoppingListService = Depends(get_shopping_list_service),
):
    item = await svc.get_by_id_or_raise(item_id)
    return templates.TemplateResponse(
        request, "partials/shopping_item_row.html", _ctx(item=item),
    )


# ── Marcar como comprado ──────────────────────────────────────────────────────

@router.post("/{item_id}/bought", response_class=HTMLResponse)
async def mark_as_bought(
    item_id: uuid.UUID,
    request: Request,
    expiry_date: str = Form(""),
    svc: ShoppingListService = Depends(get_shopping_list_service),
    food_svc: FoodInventoryService = Depends(get_food_inventory_service),
    dish_svc: DishInventoryService = Depends(get_dish_inventory_service),
):
    item = await svc.get_by_id_or_raise(item_id)
    expiry = datetime.date.fromisoformat(expiry_date) if expiry_date.strip() else None

    if item.item_type == ShoppingItemType.food:
        await food_svc.create(FoodInventoryCreate(
            name=item.name,
            quantity=item.quantity or 1.0,
            unit=item.unit,
            category=item.category,
            expiry_date=expiry,
        ))
        await food_svc.commit()
    else:
        await dish_svc.create(DishInventoryCreate(
            recipe_name_snapshot=item.name,
            servings_remaining=max(1, int(item.quantity or 1)),
            location=DishLocation.fridge,
            expiry_date=expiry or (datetime.date.today() + datetime.timedelta(days=5)),
        ))
        await dish_svc.commit()

    item = await svc.mark_purchased(item_id)
    await svc.commit()
    return templates.TemplateResponse(
        request, "partials/shopping_item_bought_row.html", _ctx(item=item),
    )

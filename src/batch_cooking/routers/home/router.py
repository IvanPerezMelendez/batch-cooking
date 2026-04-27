import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from ...core.templates import templates
from ...services.dependencies.food_inventory import get_food_inventory_service
from ...services.food_inventory import FoodInventoryService

router = APIRouter(prefix="/home", tags=["home"])


@router.get("", response_class=HTMLResponse)
async def get_home(
    request: Request,
    food_svc: FoodInventoryService = Depends(get_food_inventory_service),
):
    today = datetime.date.today()
    expired = await food_svc.repository.get_expired(today)
    return templates.TemplateResponse(
        request, "home.html",
        {"request": request, "expired": expired, "today": today},
    )

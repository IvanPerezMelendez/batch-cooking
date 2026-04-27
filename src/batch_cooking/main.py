from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers.cooking.router import router as cooking_router
from .routers.home.router import router as home_router
from .routers.inventory.router import router as inventory_router
from .routers.planner.router import router as planner_router
from .routers.recipes.router import router as recipes_router
from .routers.shopping_list.router import router as shopping_list_router
from .routers.week.router import router as week_router

app = FastAPI(title="Batch Cooking")

if not settings.is_local:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["batchcooking.ivanperezmelendez.com"])

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.parent.parent / "static"),
    name="static",
)

@app.get("/")
async def root():
    return RedirectResponse(url="/home")

app.include_router(home_router)
app.include_router(inventory_router)
app.include_router(shopping_list_router)
app.include_router(planner_router)
app.include_router(cooking_router)
app.include_router(recipes_router)
app.include_router(week_router)

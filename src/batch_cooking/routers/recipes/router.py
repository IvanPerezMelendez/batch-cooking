import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.templates import templates
from ...database import get_db
from ...models.recipe import Recipe
from ...repositories.ingredient import IngredientRepository
from ...repositories.recipe import RecipeRepository
from ...repositories.tag import TagRepository
from ...services.ingredient import IngredientService
from ...services.recipe import RecipeService
from ...services.tag import TagService
from ...services.schemas import RecipeCreate, RecipeIngredientCreate, RecipeUpdate

router = APIRouter(prefix="/recipes", tags=["recipes"])


# ── helpers ───────────────────────────────────────────────────────────────────

async def _load_recipe_detail(recipe_id: uuid.UUID, db: AsyncSession) -> dict:
    recipe_repo = RecipeRepository(db)
    ing_repo = IngredientRepository(db)
    tag_repo = TagRepository(db)

    recipe_ings = await recipe_repo.get_ingredients(recipe_id)
    recipe_tags = await recipe_repo.get_tags(recipe_id)

    ingredients = []
    for ri in recipe_ings:
        ing = await ing_repo.get_by_id(ri.ingredient_id)
        if ing:
            ingredients.append((ri, ing))

    tag_ids = [rt.tag_id for rt in recipe_tags]
    tags = await tag_repo.get_by_ids(tag_ids) if tag_ids else []

    return {"ingredients": ingredients, "tags": tags}


async def _parse_and_save(
    db: AsyncSession,
    name: str,
    servings_produced: int,
    days_fridge: int,
    days_freezer: int,
    notes: str,
    tag_names: str,
    ingredient_names: list[str],
    ingredient_quantities: list[str],
    ingredient_units: list[str],
    recipe_id: uuid.UUID | None = None,
) -> Recipe:
    ing_svc = IngredientService(IngredientRepository(db))
    tag_svc = TagService(TagRepository(db))
    recipe_svc = RecipeService(RecipeRepository(db))

    tag_ids = []
    for tname in [t.strip() for t in tag_names.split(",") if t.strip()]:
        tag = await tag_svc.get_or_create_by_name(tname)
        tag_ids.append(tag.id)

    ing_creates = []
    for iname, iqty, iunit in zip(ingredient_names, ingredient_quantities, ingredient_units):
        iname = iname.strip()
        iqty = iqty.strip()
        if not iname or not iqty:
            continue
        ingredient = await ing_svc.get_or_create_by_name(iname)
        ing_creates.append(RecipeIngredientCreate(
            ingredient_id=ingredient.id,
            quantity=float(iqty),
            unit=iunit.strip() or "ud",
        ))

    if recipe_id is None:
        data = RecipeCreate(
            name=name.strip(),
            servings_produced=servings_produced,
            days_fridge=days_fridge,
            days_freezer=days_freezer,
            notes=notes.strip() or None,
            ingredients=ing_creates,
            tag_ids=tag_ids,
        )
        recipe = await recipe_svc.create(data)
    else:
        data = RecipeUpdate(
            name=name.strip(),
            servings_produced=servings_produced,
            days_fridge=days_fridge,
            days_freezer=days_freezer,
            notes=notes.strip() or None,
            ingredients=ing_creates,
            tag_ids=tag_ids,
        )
        recipe = await recipe_svc.update(recipe_id, data)

    await db.commit()
    await db.refresh(recipe)
    return recipe


# ── Página principal ──────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def get_recipes(request: Request, db: AsyncSession = Depends(get_db)):
    recipe_repo = RecipeRepository(db)
    recipes = await recipe_repo.get_all(limit=500)

    recipe_contexts = []
    for recipe in recipes:
        detail = await _load_recipe_detail(recipe.id, db)
        recipe_contexts.append({"recipe": recipe, **detail})

    return templates.TemplateResponse(
        request, "recipes.html", {"recipe_contexts": recipe_contexts},
    )


# ── Modal nueva receta ────────────────────────────────────────────────────────

@router.get("/modal/new", response_class=HTMLResponse)
async def modal_new_recipe(request: Request):
    return templates.TemplateResponse(
        request, "partials/recipe_form_modal.html",
        {"recipe": None, "ingredients": [], "tags": []},
    )


# ── Modal editar receta ───────────────────────────────────────────────────────

@router.get("/{recipe_id}/modal/edit", response_class=HTMLResponse)
async def modal_edit_recipe(
    recipe_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)
):
    recipe_repo = RecipeRepository(db)
    recipe = await recipe_repo.get_by_id(recipe_id)
    if recipe is None:
        return Response(status_code=404)
    detail = await _load_recipe_detail(recipe_id, db)
    return templates.TemplateResponse(
        request, "partials/recipe_form_modal.html",
        {"recipe": recipe, **detail},
    )


# ── Crear receta ──────────────────────────────────────────────────────────────

@router.post("", response_class=HTMLResponse)
async def create_recipe(
    request: Request,
    name: str = Form(...),
    servings_produced: int = Form(...),
    days_fridge: int = Form(...),
    days_freezer: int = Form(...),
    notes: str = Form(""),
    tag_names: str = Form(""),
    ingredient_names: list[str] = Form(default=[]),
    ingredient_quantities: list[str] = Form(default=[]),
    ingredient_units: list[str] = Form(default=[]),
    db: AsyncSession = Depends(get_db),
):
    recipe = await _parse_and_save(
        db, name, servings_produced, days_fridge, days_freezer,
        notes, tag_names, ingredient_names, ingredient_quantities, ingredient_units,
    )
    detail = await _load_recipe_detail(recipe.id, db)
    return templates.TemplateResponse(
        request, "partials/recipe_row.html",
        {"recipe": recipe, **detail},
    )


# ── Actualizar receta ─────────────────────────────────────────────────────────

@router.put("/{recipe_id}", response_class=HTMLResponse)
async def update_recipe(
    recipe_id: uuid.UUID,
    request: Request,
    name: str = Form(...),
    servings_produced: int = Form(...),
    days_fridge: int = Form(...),
    days_freezer: int = Form(...),
    notes: str = Form(""),
    tag_names: str = Form(""),
    ingredient_names: list[str] = Form(default=[]),
    ingredient_quantities: list[str] = Form(default=[]),
    ingredient_units: list[str] = Form(default=[]),
    db: AsyncSession = Depends(get_db),
):
    recipe = await _parse_and_save(
        db, name, servings_produced, days_fridge, days_freezer,
        notes, tag_names, ingredient_names, ingredient_quantities, ingredient_units,
        recipe_id=recipe_id,
    )
    detail = await _load_recipe_detail(recipe.id, db)
    return templates.TemplateResponse(
        request, "partials/recipe_row.html",
        {"recipe": recipe, **detail},
    )


# ── Eliminar receta ───────────────────────────────────────────────────────────

@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    recipe_repo = RecipeRepository(db)
    await recipe_repo.delete(recipe_id)
    await db.commit()
    return Response(status_code=200)

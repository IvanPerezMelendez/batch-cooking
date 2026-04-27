import datetime
import uuid
from typing import Any

from pydantic import BaseModel

from ..models.dish_inventory import DishLocation
from ..models.meal_slot import MealSlotStatus
from ..models.plan import PlanStatus
from ..models.shopping_list_item import ShoppingItemType


# --- Ingredient ---

class IngredientCreate(BaseModel):
    name: str
    default_unit: str | None = None
    category: str | None = None


class IngredientUpdate(BaseModel):
    name: str | None = None
    default_unit: str | None = None
    category: str | None = None


# --- Tag ---

class TagCreate(BaseModel):
    name: str


class TagUpdate(BaseModel):
    name: str | None = None


# --- Recipe ---

class RecipeIngredientCreate(BaseModel):
    ingredient_id: uuid.UUID
    quantity: float
    unit: str


class RecipeCreate(BaseModel):
    name: str
    servings_produced: int
    days_fridge: int
    days_freezer: int
    notes: str | None = None
    ingredients: list[RecipeIngredientCreate] = []
    tag_ids: list[uuid.UUID] = []


class RecipeUpdate(BaseModel):
    name: str | None = None
    servings_produced: int | None = None
    days_fridge: int | None = None
    days_freezer: int | None = None
    notes: str | None = None
    ingredients: list[RecipeIngredientCreate] | None = None
    tag_ids: list[uuid.UUID] | None = None


# --- Plan ---

class PlanCreate(BaseModel):
    week_start: datetime.date


class PlanUpdate(BaseModel):
    status: PlanStatus | None = None


# --- MealSlot ---

class MealSlotCreate(BaseModel):
    plan_id: uuid.UUID
    date: datetime.date
    slot_label: str
    recipe_id: uuid.UUID | None = None


class MealSlotUpdate(BaseModel):
    recipe_id: uuid.UUID | None = None
    status: MealSlotStatus | None = None
    slot_label: str | None = None


# --- ShoppingListItem ---

class ShoppingListItemCreate(BaseModel):
    name: str
    item_type: ShoppingItemType = ShoppingItemType.food
    ingredient_id: uuid.UUID | None = None
    quantity: float | None = None
    unit: str | None = None
    category: str | None = None
    supermarket: str | None = None
    source_plan_id: uuid.UUID | None = None


class ShoppingListItemUpdate(BaseModel):
    name: str | None = None
    item_type: ShoppingItemType | None = None
    quantity: float | None = None
    unit: str | None = None
    category: str | None = None
    supermarket: str | None = None
    is_purchased: bool | None = None


# --- FoodInventory ---

class FoodInventoryCreate(BaseModel):
    name: str
    ingredient_id: uuid.UUID | None = None
    quantity: float
    unit: str | None = None
    category: str | None = None
    expiry_date: datetime.date | None = None


class FoodInventoryUpdate(BaseModel):
    name: str | None = None
    quantity: float | None = None
    unit: str | None = None
    category: str | None = None
    expiry_date: datetime.date | None = None


# --- DishInventory ---

class DishInventoryCreate(BaseModel):
    recipe_name_snapshot: str
    servings_remaining: int
    location: DishLocation
    expiry_date: datetime.date
    recipe_id: uuid.UUID | None = None


class DishInventoryUpdate(BaseModel):
    servings_remaining: int | None = None
    location: DishLocation | None = None
    expiry_date: datetime.date | None = None


# --- Settings ---

class SettingsCreate(BaseModel):
    key: str
    value: Any = None


class SettingsUpdate(BaseModel):
    value: Any = None

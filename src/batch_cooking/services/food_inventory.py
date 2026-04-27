import datetime
import uuid

from ..models.food_inventory import FoodInventory
from ..repositories.food_inventory import FoodInventoryRepository
from .base import BaseService
from .schemas import FoodInventoryCreate, FoodInventoryUpdate


class FoodInventoryService(BaseService[FoodInventory, FoodInventoryRepository, FoodInventoryCreate, FoodInventoryUpdate]):
    def __init__(self, repository: FoodInventoryRepository) -> None:
        super().__init__(repository)

    async def get_all_categories(self, q: str = "") -> list[str]:
        return await self.repository.get_all_categories(q)

    async def get_expired(self, today: datetime.date | None = None) -> list[FoodInventory]:
        return await self.repository.get_expired(today or datetime.date.today())

    async def deduct_by_ingredient_id(self, ingredient_id: uuid.UUID, quantity: float) -> None:
        await self.repository.deduct_by_ingredient_id(ingredient_id, quantity)

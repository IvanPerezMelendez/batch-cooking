import uuid

from ..models.dish_inventory import DishInventory
from ..repositories.dish_inventory import DishInventoryRepository
from .base import BaseService
from .schemas import DishInventoryCreate, DishInventoryUpdate


class DishInventoryService(BaseService[DishInventory, DishInventoryRepository, DishInventoryCreate, DishInventoryUpdate]):
    def __init__(self, repository: DishInventoryRepository) -> None:
        super().__init__(repository)

    async def get_by_recipe(self, recipe_id: uuid.UUID) -> list[DishInventory]:
        return await self.repository.get_by_recipe(recipe_id)

    async def consume_serving(self, recipe_id: uuid.UUID) -> DishInventory | None:
        """Resta 1 ración del lote con caducidad más próxima (FIFO)."""
        batches = await self.repository.get_available_fifo(recipe_id)
        if not batches:
            return None
        batch = batches[0]
        batch.servings_remaining -= 1
        if batch.servings_remaining == 0:
            self.repository.db.delete(batch)
            await self.repository.db.flush()
            return None
        return await self.repository.update(batch)

import uuid

from ..models.shopping_list_item import ShoppingListItem
from ..repositories.shopping_list import ShoppingListRepository
from .base import BaseService
from .schemas import ShoppingListItemCreate, ShoppingListItemUpdate


class ShoppingListService(BaseService[ShoppingListItem, ShoppingListRepository, ShoppingListItemCreate, ShoppingListItemUpdate]):
    def __init__(self, repository: ShoppingListRepository) -> None:
        super().__init__(repository)

    async def get_pending(self) -> list[ShoppingListItem]:
        return await self.repository.get_pending()

    async def get_by_plan(self, plan_id: uuid.UUID) -> list[ShoppingListItem]:
        return await self.repository.get_by_plan(plan_id)

    async def get_all_categories(self, q: str = "") -> list[str]:
        return await self.repository.get_all_categories(q)

    async def get_all_supermarkets(self, q: str = "") -> list[str]:
        return await self.repository.get_all_supermarkets(q)

    async def bulk_add_from_plan(
        self, items: list[ShoppingListItemCreate], plan_id: uuid.UUID
    ) -> list[ShoppingListItem]:
        objs = [
            ShoppingListItem(**{**item.model_dump(exclude_unset=True), "source_plan_id": plan_id})
            for item in items
        ]
        return await self.repository.create_bulk(objs)

    async def mark_purchased(self, id: uuid.UUID) -> ShoppingListItem:
        item = await self.get_by_id_or_raise(id)
        item.is_purchased = True
        return await self.repository.update(item)

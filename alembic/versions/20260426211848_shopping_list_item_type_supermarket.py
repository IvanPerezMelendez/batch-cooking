"""shopping_list_item_type_supermarket

Revision ID: 20260426211848
Revises: 20260426210018
Create Date: 2026-04-26 21:18:49.023885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260426211848'
down_revision: Union[str, None] = '20260426210018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    shopping_item_type = sa.Enum('food', 'dish', name='shoppingitemtype')
    shopping_item_type.create(op.get_bind(), checkfirst=True)
    op.add_column('shopping_list_item', sa.Column('item_type', shopping_item_type, nullable=True))
    op.execute("UPDATE shopping_list_item SET item_type = 'food' WHERE item_type IS NULL")
    op.alter_column('shopping_list_item', 'item_type', nullable=False)
    op.add_column('shopping_list_item', sa.Column('supermarket', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('shopping_list_item', 'supermarket')
    op.drop_column('shopping_list_item', 'item_type')
    sa.Enum(name='shoppingitemtype').drop(op.get_bind(), checkfirst=True)

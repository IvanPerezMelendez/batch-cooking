"""remove plan model

Revision ID: 20260502000000
Revises: 20260426211848
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260502000000'
down_revision: Union[str, None] = '20260426211848'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop FK shopping_list_item.source_plan_id -> plan
    op.drop_constraint(
        'fk_shopping_list_item_source_plan_id_plan',
        'shopping_list_item',
        type_='foreignkey',
    )
    op.drop_column('shopping_list_item', 'source_plan_id')
    op.add_column('shopping_list_item', sa.Column('source_date', sa.Date(), nullable=True))

    # Drop FK meal_slot.plan_id -> plan
    op.drop_constraint('fk_meal_slot_plan_id_plan', 'meal_slot', type_='foreignkey')
    op.drop_column('meal_slot', 'plan_id')

    # Drop plan table and its enum
    op.drop_table('plan')
    sa.Enum(name='planstatus').drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    # Destructive migration – downgrade not supported
    pass

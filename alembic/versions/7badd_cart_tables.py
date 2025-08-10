"""Remove cart tables (no persistent cart).

Revision ID: 7badd
Revises: e4d1e67c2887
Create Date: 2025-08-09 12:45:00
"""

from alembic import op

revision = '7badd'
down_revision = 'e4d1e67c2887'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # If cart tables were created on a previous run, drop them; otherwise, no-op
    try:
        op.drop_table('cart_items')
    except Exception:
        pass
    try:
        op.drop_table('carts')
    except Exception:
        pass


def downgrade() -> None:
    # No-op (we don't recreate cart tables)
    pass



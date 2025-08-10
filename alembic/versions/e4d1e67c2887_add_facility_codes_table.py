"""Add facility_codes table

Revision ID: e4d1e67c2887
Revises: 08069cc08fc1
Create Date: 2025-08-09 12:09:54.484016
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'e4d1e67c2887'
down_revision = '08069cc08fc1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table('facility_codes'):
        op.create_table(
            'facility_codes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('code', sa.String(length=64), nullable=False),
            sa.Column('label', sa.String(length=255), nullable=False),
            sa.Column('scope', sa.String(length=32), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_facility_codes_code'), 'facility_codes', ['code'], unique=True)
        op.create_index(op.f('ix_facility_codes_id'), 'facility_codes', ['id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table('facility_codes'):
        op.drop_index(op.f('ix_facility_codes_id'), table_name='facility_codes')
        op.drop_index(op.f('ix_facility_codes_code'), table_name='facility_codes')
        op.drop_table('facility_codes')



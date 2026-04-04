"""Add expense_date and risk_flags

Revision ID: bdef861d8fea
Revises: aecf752d6cea
Create Date: 2026-04-04 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'bdef861d8fea'
down_revision = 'aecf752d6cea'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('expenses', sa.Column('expense_date', sa.DateTime(), nullable=True))
    op.add_column('expenses', sa.Column('risk_flags', sa.JSON(), nullable=True, default=[]))

def downgrade() -> None:
    op.drop_column('expenses', 'expense_date')
    op.drop_column('expenses', 'risk_flags')

"""update page name char limit

Revision ID: b888de398f59
Revises: 03a51cc0b8b6
Create Date: 2024-06-21 11:33:12.251000

"""

# revision identifiers, used by Alembic.
revision = 'b888de398f59'
down_revision = '03a51cc0b8b6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('page', 'name',
                    existing_type=sa.String(length=30),
                    type_=sa.String(length=100),
                    existing_nullable=False)


def downgrade():
    op.alter_column('page', 'name',
                    existing_type=sa.String(length=100),
                    type_=sa.String(length=30),
                    existing_nullable=False)

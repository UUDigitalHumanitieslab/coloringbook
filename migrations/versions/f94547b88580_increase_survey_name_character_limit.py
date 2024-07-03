"""Increase Survey name character limit

Revision ID: f94547b88580
Revises: b888de398f59
Create Date: 2024-06-27 13:27:52.743000

"""

# revision identifiers, used by Alembic.
revision = 'f94547b88580'
down_revision = 'b888de398f59'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('survey', 'name',
                    existing_type=sa.String(length=40),
                    type_=sa.String(length=100),
                    existing_nullable=False)


def downgrade():
    op.alter_column('survey', 'name',
                    existing_type=sa.String(length=100),
                    type_=sa.String(length=40),
                    existing_nullable=False)

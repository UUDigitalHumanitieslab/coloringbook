"""Add email address to Survey

Revision ID: 03a51cc0b8b6
Revises: 74e0e68b5b73
Create Date: 2023-12-01 09:03:57.295460

"""

# revision identifiers, used by Alembic.
revision = "03a51cc0b8b6"
down_revision = "74e0e68b5b73"

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        "survey", sa.Column("email_address", sa.String(length=60), nullable=True)
    )


def downgrade():
    op.drop_column("survey", "email_address")

"""Add the back button

Revision ID: 3a2ef2e83801
Revises: 5983ec6ed709
Create Date: 2017-02-21 19:02:07.556181

"""

# revision identifiers, used by Alembic.
revision = '3a2ef2e83801'
down_revision = '5983ec6ed709'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('button_set', sa.Column(
        'page_back_button',
        sa.String(length=30),
        nullable=False,
        server_default='',
    ))


def downgrade():
    op.drop_column('button_set', 'page_back_button')

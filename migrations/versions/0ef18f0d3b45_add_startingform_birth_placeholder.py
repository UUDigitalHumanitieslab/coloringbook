"""Add StartingForm.birth_placeholder

Revision ID: 0ef18f0d3b45
Revises: 5066fb19b3a6
Create Date: 2016-11-17 11:58:04.240197

"""

# revision identifiers, used by Alembic.
revision = '0ef18f0d3b45'
down_revision = '5066fb19b3a6'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    op.add_column('starting_form', sa.Column(
        'birth_placeholder',
        sa.String(length=10),
        nullable=False,
        server_default='yyyy-mm-dd',  # new, internationally oriented default
    ))
    starting_form = sql.table(
        'starting_form',
        sql.column('id', sa.Integer),
        sql.column('birth_placeholder', sa.String(10)),
    )
    op.execute(starting_form.update().where(starting_form.c.id==1).values({
        'birth_placeholder': 'jjjj-mm-dd',  # default value before customization
    }))


def downgrade():
    op.drop_column('starting_form', 'birth_placeholder')

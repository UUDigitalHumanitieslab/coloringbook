"""empty message

Revision ID: 0381ce789c3b
Revises: 0a45a4bc64ba
Create Date: 2016-12-21 12:29:07.198808

"""

# revision identifiers, used by Alembic.
revision = '0381ce789c3b'
down_revision = '0a45a4bc64ba'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    op.add_column('button_set', sa.Column(
        'post_survey_button',
        sa.String(length=40),
        nullable=False,
        server_default='Next subject',
    ))
    button_set = sql.table(
        'button_set',
        sql.column('id', sa.Integer),
        sql.column('post_survey_button', sa.String(10)),
    )
    op.execute(button_set.update().where(button_set.c.id==1).values({
        'post_survey_button': 'Volgende proefpersoon',  # Dutch
    }))


def downgrade():
    op.drop_column('button_set', 'post_survey_button')

"""Reset original survey title in pre-existing surveys

We are doing this because surveys before this update always displayed
"Kleurgeheugenexperiment" as the title. The new default is better, i.e.
"Coloring Book", but using this for existing surveys may be disruptive.

Revision ID: 5066fb19b3a6
Revises: dac07043736a
Create Date: 2016-11-17 11:15:41.973102

"""

# revision identifiers, used by Alembic.
revision = '5066fb19b3a6'
down_revision = 'dac07043736a'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    survey = sql.table(
        'survey',
        sql.column('title', sa.String(100)),
    )
    op.execute(survey.update().values({
        'title': op.inline_literal('Kleurgeheugenexperiment'),
    }))


def downgrade():
    pass

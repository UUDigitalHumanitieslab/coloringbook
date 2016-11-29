""" Use Text instead of String(500) for Survey.information

Revision ID: 8766f4aef5e7
Revises: 0befa4fe217c
Create Date: 2016-03-01 13:36:43.641319

"""

# revision identifiers, used by Alembic.
revision = '8766f4aef5e7'
down_revision = '0befa4fe217c'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.alter_column('survey', 'information',
               existing_type=sa.String(500),
               type_=sa.Text)


def downgrade():
    op.alter_column('survey', 'information',
               existing_type=sa.Text,
               type_=sa.String(500))

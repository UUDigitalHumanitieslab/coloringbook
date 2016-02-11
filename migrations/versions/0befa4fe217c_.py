""" Add per-survey sentence duration

Revision ID: 0befa4fe217c
Revises: d52beb9c9f43
Create Date: 2016-02-10 11:55:06.444046

"""

# revision identifiers, used by Alembic.
revision = '0befa4fe217c'
down_revision = 'd52beb9c9f43'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('survey', sa.Column('duration', sa.Integer(), nullable=False, server_default=sa.text('6000')))


def downgrade():
    op.drop_column('survey', 'duration')

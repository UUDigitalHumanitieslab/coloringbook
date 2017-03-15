"""Add the generic action model

Revision ID: 74e0e68b5b73
Revises: 3a2ef2e83801
Create Date: 2017-03-01 11:52:11.024334

"""

# revision identifiers, used by Alembic.
revision = '74e0e68b5b73'
down_revision = '3a2ef2e83801'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('action',
        sa.Column('survey_id', sa.Integer(), nullable=False),
        sa.Column('page_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('time', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('action', sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(['page_id'], ['page.id']),
        sa.ForeignKeyConstraint(['subject_id'], ['subject.id']),
        sa.ForeignKeyConstraint(['survey_id'], ['survey.id']),
        sa.PrimaryKeyConstraint('survey_id', 'page_id', 'subject_id', 'time'),
        mysql_engine='InnoDB',
    )


def downgrade():
    op.drop_table('action')

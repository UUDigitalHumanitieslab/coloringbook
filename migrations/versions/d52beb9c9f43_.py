""" Expand the name lengths of area, drawing and sound

Revision ID: d52beb9c9f43
Revises: b870030c5a97
Create Date: 2016-02-04 13:51:03.852042

"""

# revision identifiers, used by Alembic.
revision = 'd52beb9c9f43'
down_revision = 'b870030c5a97'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('area', 'name',
               existing_type=sa.String(length=20),
               type_=sa.String(length=40),
               existing_nullable=False)
    op.alter_column('drawing', 'name',
               existing_type=sa.String(length=30),
               type_=sa.String(length=50),
               existing_nullable=False)
    op.alter_column('sound', 'name',
               existing_type=sa.String(length=30),
               type_=sa.String(length=50),
               existing_nullable=False)


def downgrade():
    op.alter_column('sound', 'name',
               existing_type=sa.String(length=50),
               type_=sa.String(length=30),
               existing_nullable=False)
    op.alter_column('drawing', 'name',
               existing_type=sa.String(length=50),
               type_=sa.String(length=30),
               existing_nullable=False)
    op.alter_column('area', 'name',
               existing_type=sa.String(length=40),
               type_=sa.String(length=20),
               existing_nullable=False)

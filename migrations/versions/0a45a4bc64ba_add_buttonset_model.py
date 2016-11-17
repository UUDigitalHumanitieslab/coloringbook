"""Add ButtonSet model

Revision ID: 0a45a4bc64ba
Revises: 0ef18f0d3b45
Create Date: 2016-11-17 13:40:35.933134

"""

# revision identifiers, used by Alembic.
revision = '0a45a4bc64ba'
down_revision = '0ef18f0d3b45'

from alembic import op
import sqlalchemy as sa


def upgrade():
    button_set = op.create_table('button_set',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=30), nullable=False),
        sa.Column('post_instruction_button', sa.String(length=30), nullable=False),
        sa.Column('post_page_button', sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_engine='InnoDB',
    )
    op.bulk_insert(button_set, [{
        'name': 'default (NL)',
        'post_instruction_button': 'Start!',
        'post_page_button': 'klaar',
    }])
    op.add_column(u'survey', sa.Column(
        'button_set_id',
        sa.Integer(),
        nullable=False,
        server_default='1',
    ))
    op.create_foreign_key(
        'fk_button_set',
        'survey',
        'button_set',
        ['button_set_id'],
        ['id'],
    )


def downgrade():
    op.drop_constraint('fk_button_set', 'survey', type_='foreignkey')
    op.drop_column(u'survey', 'button_set_id')
    op.drop_table('button_set')

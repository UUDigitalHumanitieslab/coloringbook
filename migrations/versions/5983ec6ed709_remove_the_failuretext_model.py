# encoding: utf-8

"""Remove the FailureText model

Revision ID: 5983ec6ed709
Revises: 0381ce789c3b
Create Date: 2017-02-01 13:59:07.006505

"""

# revision identifiers, used by Alembic.
revision = '5983ec6ed709'
down_revision = '0381ce789c3b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint(u'fk_failure_text', 'survey', type_='foreignkey')
    op.drop_column('survey', 'failure_text_id')
    op.drop_table('failure_text')


def downgrade():
    survey_failure_text = op.create_table('survey_failure_text',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=30), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_engine='InnoDB'
    )
    op.bulk_insert(
        survey_failure_text,
        [{
            'name': 'default (NL)',
            'content': 'Dank voor je deelname aan dit experiment.<br>\nDoor een technisch probleem is het opslaan van je invoer helaas niet gelukt. Zou je de inhoud van onderstaand kader willen kopiëren en opslaan, en dit als bijlage willen opsturen naar de ontwikkelaar?<br>\nBij voorbaat dank!',
        }]
    )
    op.add_column('survey', sa.Column(
        'failure_text_id',
        sa.Integer(),
        nullable=False,
        server_default='1'
    ))
    op.create_foreign_key(
        'fk_failure_text',
        'survey',
        'survey_failure_text',
        ['failure_text_id'],
        ['id']
    )

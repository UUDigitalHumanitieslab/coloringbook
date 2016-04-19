"""Add starting form customization model

Revision ID: 32806278e9f6
Revises: d6e610d98877
Create Date: 2016-04-19 16:47:10.181548

"""

# revision identifiers, used by Alembic.
revision = '32806278e9f6'
down_revision = 'd6e610d98877'

from alembic import op
import sqlalchemy as sa


def upgrade():
    starting_form = op.create_table('starting_form',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=30), nullable=False),
        sa.Column('name_label', sa.String(length=30), nullable=False),
        sa.Column('numeral_label', sa.String(length=30), nullable=True),
        sa.Column('birth_label', sa.String(length=30), nullable=False),
        sa.Column('eyesight_label', sa.String(length=30), nullable=False),
        sa.Column('eyesight_label_2', sa.Text(), nullable=True),
        sa.Column('language_label', sa.String(length=30), nullable=False),
        sa.Column('language_label_2', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_engine='InnoDB'
    )
    op.bulk_insert(starting_form, [
        {
            'name': 'default (NL)',
            'name_label': 'Naam',
            'numeral_label': 'Studentnummer',
            'birth_label': 'Geboortedatum',
            'eyesight_label': 'Bijzonderheden',
            'eyesight_label_2': '(kleurenblind, slechtziend, enzovoorts)',
            'language_label': 'Moedertaal',
            'language_label_2': '''Spreek je nog andere talen?<br>,
Voeg iedere taal toe met het plusje en geef aan wat je niveau is,
(1: redelijk &ndash; 10: moedertaalniveau).''',
        },
    ])
    op.add_column(u'survey', sa.Column(
        'starting_form_id',
        sa.Integer(),
        nullable=False,
        server_default='1'
    ))
    op.create_foreign_key(
        'survey_starting_form_fkey',
        'survey',
        'starting_form',
        ['starting_form_id'],
        ['id']
    )


def downgrade():
    op.drop_constraint('survey_starting_form_fkey', 'survey', type_='foreignkey')
    op.drop_column(u'survey', 'starting_form_id')
    op.drop_table('starting_form')

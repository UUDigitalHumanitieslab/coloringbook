# -*- encoding: utf-8 -*-

""" Add text customization, with defaults

Revision ID: 7b47d97c4073
Revises: 8766f4aef5e7
Create Date: 2016-03-01 14:05:23.851777

"""

# revision identifiers, used by Alembic.
revision = '7b47d97c4073'
down_revision = '8766f4aef5e7'

from alembic import op
import sqlalchemy as sa

def upgrade():
    survey_failure_text = op.create_table('survey_failure_text',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=30), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_engine='InnoDB'
    )
    survey_instruction_text = op.create_table('survey_instruction_text',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=30), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_engine='InnoDB'
    )
    survey_privacy_text = op.create_table('survey_privacy_text',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=30), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_engine='InnoDB'
    )
    survey_success_text = op.create_table('survey_success_text',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=30), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_engine='InnoDB'
    )
    survey_welcome_text = op.create_table('survey_welcome_text',
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
            'content': 'Dank voor je deelname aan dit experiment.<br>\nDoor een technisch probleem is het opslaan van je invoer helaas niet gelukt. Zou je de inhoud van onderstaand kader willen kopiëren en opslaan, en dit als bijlage willen opsturen naar j.gonggrijp@uu.nl?<br>\nBij voorbaat dank!',
        }]
    )
    op.bulk_insert(
        survey_instruction_text,
        [{
            'name': 'default (NL)',
            'content': 'Je krijgt straks steeds een zin te zien of te horen waarin een aantal kleuren voorkomen.\nBijvoorbeeld: &ldquo;een vrouw met een kort rokje en rode schoenen staat naast een vrouw met een blauwe handtas&rdquo;.\nLees of luister de zin zorgvuldig en probeer hem te onthouden.\nNa 6 seconden verdwijnt de zin en verschijnt een kleurplaat die bij de zin past.\nGebruik de knoppen onderaan het scherm om een kleur te kiezen en vul de juiste vakjes van de tekening in met de laatstgekozen kleur door erin te klikken.\nIn de voorbeeldzin zou je de schoenen van de vrouw met het korte rokje rood inkleuren en zou je de tas van de vrouw ernaast blauw inkleuren.<br><br>\nVervolgens druk je op &ldquo;klaar&rdquo;, je krijgt dan de volgende zin te zien.\nAan het einde stellen we nog een paar vragen ter evaluatie.\nJe kunt niet terugkijken of later van gedachten veranderen.\nLet op: dezelfde kleurplaat kan meerdere keren voorkomen met verschillende zinnen.<br><br>\nSucces!',
        }]
    )
    op.bulk_insert(
        survey_privacy_text,
        [{
            'name': 'default (NL)',
            'content': 'PRIVACY<br>\nDe gegevens die wij met deze app verzamelen zullen vertrouwelijk worden behandeld. Persoonlijke gegevens zullen niet worden vermeld, noch tijdens de studie, noch bij een eventuele publicatie van de resultaten van dit onderzoek.',
        }]
    )
    op.bulk_insert(
        survey_success_text,
        [{
            'name': 'default (NL)',
            'content': 'Dank voor je deelname aan dit experiment.',
        }]
    )
    op.bulk_insert(
        survey_welcome_text,
        [{
            'name': 'default (NL)',
            'content': 'Welkom bij Coloring Book.\nZou je alstublieft het volgende formulier willen invullen?',
        }]
    )
    op.add_column(u'survey', sa.Column(
        'failure_text_id',
        sa.Integer(),
        nullable=False,
        server_default='1'
    ))
    op.add_column(u'survey', sa.Column(
        'instruction_text_id',
        sa.Integer(),
        nullable=False,
        server_default='1'
    ))
    op.add_column(u'survey', sa.Column(
        'privacy_text_id',
        sa.Integer(),
        nullable=False,
        server_default='1'
    ))
    op.add_column(u'survey', sa.Column(
        'success_text_id',
        sa.Integer(),
        nullable=False,
        server_default='1'
    ))
    op.add_column(u'survey', sa.Column(
        'title',
        sa.String(length=100),
        nullable=False,
        server_default='Coloring Book'
    ))
    op.add_column(u'survey', sa.Column(
        'welcome_text_id',
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
    op.create_foreign_key(
        'fk_instruction_text',
        'survey',
        'survey_instruction_text',
        ['instruction_text_id'],
        ['id']
    )
    op.create_foreign_key(
        'fk_success_text',
        'survey',
        'survey_success_text',
        ['success_text_id'],
        ['id']
    )
    op.create_foreign_key(
        'fk_welcome_text',
        'survey',
        'survey_welcome_text',
        ['welcome_text_id'],
        ['id']
    )
    op.create_foreign_key(
        'fk_privacy_text',
        'survey',
        'survey_privacy_text',
        ['privacy_text_id'],
        ['id']
    )


def downgrade():
    op.drop_constraint('fk_privacy_text', 'survey', type_='foreignkey')
    op.drop_constraint('fk_welcome_text', 'survey', type_='foreignkey')
    op.drop_constraint('fk_success_text', 'survey', type_='foreignkey')
    op.drop_constraint('fk_instruction_text', 'survey', type_='foreignkey')
    op.drop_constraint('fk_failure_text', 'survey', type_='foreignkey')
    op.drop_column(u'survey', 'welcome_text_id')
    op.drop_column(u'survey', 'title')
    op.drop_column(u'survey', 'success_text_id')
    op.drop_column(u'survey', 'privacy_text_id')
    op.drop_column(u'survey', 'instruction_text_id')
    op.drop_column(u'survey', 'failure_text_id')
    op.drop_table('survey_welcome_text')
    op.drop_table('survey_success_text')
    op.drop_table('survey_privacy_text')
    op.drop_table('survey_instruction_text')
    op.drop_table('survey_failure_text')

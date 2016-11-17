"""Add ending form customization

Revision ID: dac07043736a
Revises: 32806278e9f6
Create Date: 2016-04-20 17:02:42.932687

"""

# revision identifiers, used by Alembic.
revision = 'dac07043736a'
down_revision = '32806278e9f6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ending_form = op.create_table('ending_form',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=30), nullable=False),
        sa.Column('introduction', sa.Text(), nullable=False),
        sa.Column('difficulty_label', sa.Text(), nullable=False),
        sa.Column('topic_label', sa.Text(), nullable=False),
        sa.Column('comments_label', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_engine='InnoDB'
    )
    op.bulk_insert(ending_form, [
        {
            'name': 'default (NL)',
            'introduction': 'Ter evaluatie zouden we je graag nog een paar laatste vragen willen stellen.',
            'difficulty_label': '''Hoe moeilijk vond je het om de zinnen en kleuren te onthouden?
Kies 1 voor heel makkelijk en 10 voor heel moeilijk.''',
            'topic_label': 'Waarover denk je dat deze test gaat?',
            'comments_label': 'Andere opmerkingen:',
        },
    ])
    op.add_column(u'survey', sa.Column(
        'ending_form_id',
        sa.Integer(),
        server_default='1',
        nullable=False
    ))
    op.create_foreign_key(
        'survey_ending_form_fkey',
        'survey',
        'ending_form',
        ['ending_form_id'],
        ['id']
    )


def downgrade():
    op.drop_constraint('survey_ending_form_fkey', 'survey', type_='foreignkey')
    op.drop_column(u'survey', 'ending_form_id')
    op.drop_table('ending_form')

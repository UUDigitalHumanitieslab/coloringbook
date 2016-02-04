"""Layout of version 1.0 with colors

Revision ID: b870030c5a97
Revises: None
Create Date: 2016-01-27 15:37:12.555367

"""

# revision identifiers, used by Alembic.
revision = 'b870030c5a97'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    color_table = op.create_table('color',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=25), nullable=False),
    sa.Column('name', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.bulk_insert(
        color_table,
        [
            {'name': 'red',    'code': '#d01'},
            {'name': 'orange', 'code': '#f90'},
            {'name': 'yellow', 'code': '#ee4'},
            {'name': 'green',  'code': '#5d2'},
            {'name': 'blue',   'code': '#06e'},
            {'name': 'purple', 'code': '#717'},
            {'name': 'brown',  'code': '#953'},
            {'name': 'white',  'code': '#fff'},
        ]
    )
    op.create_table('drawing',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('language',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    mysql_engine='InnoDB'
    )
    op.create_table('sound',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('subject',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('numeral', sa.Integer(), nullable=True),
    sa.Column('birth', sa.DateTime(), nullable=False),
    sa.Column('eyesight', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('area',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=20), nullable=False),
    sa.Column('drawing_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['drawing_id'], ['drawing.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'drawing_id'),
    mysql_engine='InnoDB'
    )
    op.create_table('page',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=False),
    sa.Column('language_id', sa.Integer(), nullable=True),
    sa.Column('text', sa.String(length=200), nullable=True),
    sa.Column('sound_id', sa.Integer(), nullable=True),
    sa.Column('drawing_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['drawing_id'], ['drawing.id'], ),
    sa.ForeignKeyConstraint(['language_id'], ['language.id'], ),
    sa.ForeignKeyConstraint(['sound_id'], ['sound.id'], ),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('subject_language',
    sa.Column('language_id', sa.Integer(), nullable=False),
    sa.Column('subject_id', sa.Integer(), nullable=False),
    sa.Column('level', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['language_id'], ['language.id'], ),
    sa.ForeignKeyConstraint(['subject_id'], ['subject.id'], ),
    sa.PrimaryKeyConstraint('language_id', 'subject_id'),
    mysql_engine='InnoDB'
    )
    op.create_table('survey',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=40), nullable=False),
    sa.Column('language_id', sa.Integer(), nullable=True),
    sa.Column('begin', sa.DateTime(), nullable=True),
    sa.Column('end', sa.DateTime(), nullable=True),
    sa.Column('simultaneous', sa.Boolean(), nullable=False),
    sa.Column('information', sa.String(length=500), nullable=True),
    sa.ForeignKeyConstraint(['language_id'], ['language.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    mysql_engine='InnoDB'
    )
    op.create_table('expectation',
    sa.Column('page_id', sa.Integer(), nullable=False),
    sa.Column('area_id', sa.Integer(), nullable=False),
    sa.Column('color_id', sa.Integer(), nullable=False),
    sa.Column('here', sa.Boolean(), nullable=False),
    sa.Column('motivation', sa.String(length=200), nullable=True),
    sa.ForeignKeyConstraint(['area_id'], ['area.id'], ),
    sa.ForeignKeyConstraint(['color_id'], ['color.id'], ),
    sa.ForeignKeyConstraint(['page_id'], ['page.id'], ),
    sa.PrimaryKeyConstraint('page_id', 'area_id'),
    mysql_engine='InnoDB'
    )
    op.create_table('fill',
    sa.Column('survey_id', sa.Integer(), nullable=False),
    sa.Column('page_id', sa.Integer(), nullable=False),
    sa.Column('area_id', sa.Integer(), nullable=False),
    sa.Column('subject_id', sa.Integer(), nullable=False),
    sa.Column('time', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('color_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['area_id'], ['area.id'], ),
    sa.ForeignKeyConstraint(['color_id'], ['color.id'], ),
    sa.ForeignKeyConstraint(['page_id'], ['page.id'], ),
    sa.ForeignKeyConstraint(['subject_id'], ['subject.id'], ),
    sa.ForeignKeyConstraint(['survey_id'], ['survey.id'], ),
    sa.PrimaryKeyConstraint('survey_id', 'page_id', 'area_id', 'subject_id', 'time'),
    mysql_engine='InnoDB'
    )
    op.create_table('survey_page',
    sa.Column('survey_id', sa.Integer(), nullable=False),
    sa.Column('page_id', sa.Integer(), nullable=False),
    sa.Column('ordering', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['page_id'], ['page.id'], ),
    sa.ForeignKeyConstraint(['survey_id'], ['survey.id'], ),
    sa.PrimaryKeyConstraint('survey_id', 'page_id'),
    mysql_engine='InnoDB'
    )
    op.create_table('survey_subject',
    sa.Column('survey_id', sa.Integer(), nullable=False),
    sa.Column('subject_id', sa.Integer(), nullable=False),
    sa.Column('difficulty', sa.Integer(), nullable=True),
    sa.Column('topic', sa.String(length=60), nullable=True),
    sa.Column('comments', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['subject_id'], ['subject.id'], ),
    sa.ForeignKeyConstraint(['survey_id'], ['survey.id'], ),
    sa.PrimaryKeyConstraint('survey_id', 'subject_id'),
    mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('survey_subject')
    op.drop_table('survey_page')
    op.drop_table('fill')
    op.drop_table('expectation')
    op.drop_table('survey')
    op.drop_table('subject_language')
    op.drop_table('page')
    op.drop_table('area')
    op.drop_table('subject')
    op.drop_table('sound')
    op.drop_table('language')
    op.drop_table('drawing')
    op.drop_table('color')

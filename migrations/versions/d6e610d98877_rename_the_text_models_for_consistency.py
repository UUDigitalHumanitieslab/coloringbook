"""Rename the text models for consistency

Revision ID: d6e610d98877
Revises: 7b47d97c4073
Create Date: 2016-04-19 15:36:48.280442

"""

# revision identifiers, used by Alembic.
revision = 'd6e610d98877'
down_revision = '7b47d97c4073'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.rename_table('survey_failure_text', 'failure_text')
    op.rename_table('survey_welcome_text', 'welcome_text')
    op.rename_table('survey_instruction_text', 'instruction_text')
    op.rename_table('survey_privacy_text', 'privacy_text')
    op.rename_table('survey_success_text', 'success_text')


def downgrade():
    op.rename_table('welcome_text', 'survey_welcome_text')
    op.rename_table('success_text', 'survey_success_text')
    op.rename_table('privacy_text', 'survey_privacy_text')
    op.rename_table('instruction_text', 'survey_instruction_text')
    op.rename_table('failure_text', 'survey_failure_text')

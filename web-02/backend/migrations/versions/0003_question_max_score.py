"""Add per-question max score for question-based grading.

Revision ID: 0003_question_max_score
Revises: 0002_assignment_questions
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_question_max_score"
down_revision = "0002_assignment_questions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("assignment_questions", sa.Column("max_score", sa.Float(), nullable=False, server_default="10"))


def downgrade():
    op.drop_column("assignment_questions", "max_score")

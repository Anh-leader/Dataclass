"""Add per-assignment questions, per-question answers and reference answers.

Revision ID: 0002_assignment_questions
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_assignment_questions"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # New reference-answer fields on assignments (safe defaults; never auto-publish).
    op.add_column("assignments", sa.Column("reference_answer_json", sa.Text(), nullable=False, server_default=""))
    op.add_column("assignments", sa.Column("reference_published", sa.Boolean(), nullable=False, server_default=sa.text("0")))

    op.create_table("assignment_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assignment_id", sa.Integer(), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_order", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("assignment_id", "question_order"))
    op.create_index("ix_assignment_questions_assignment_id", "assignment_questions", ["assignment_id"])

    op.create_table("submission_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("assignment_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("answer_markdown", sa.Text(), nullable=False),
        sa.Column("selected_artifacts_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submission_id", "question_id"))
    op.create_index("ix_submission_answers_submission_id", "submission_answers", ["submission_id"])
    op.create_index("ix_submission_answers_question_id", "submission_answers", ["question_id"])

    # Snapshot of the three answers at the moment each version was submitted.
    op.add_column("submission_versions", sa.Column("answers_snapshot_json", sa.Text(), nullable=False, server_default="[]"))

    # Link a chat job to the assignment question being discussed (nullable for legacy rows).
    with op.batch_alter_table("ai_jobs") as batch_op:
        batch_op.add_column(sa.Column("question_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_ai_jobs_question_id", "assignment_questions", ["question_id"], ["id"], ondelete="CASCADE")


def downgrade():
    op.drop_column("ai_jobs", "question_id")
    op.drop_column("submission_versions", "answers_snapshot_json")
    op.drop_table("submission_answers")
    op.drop_table("assignment_questions")
    op.drop_column("assignments", "reference_published")
    op.drop_column("assignments", "reference_answer_json")

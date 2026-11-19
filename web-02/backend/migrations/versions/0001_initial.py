"""Initial DataClass schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(254), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False), sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("role", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"))
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("classrooms",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(160), nullable=False),
        sa.Column("join_code", sa.String(24), nullable=False), sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("join_code"))
    op.create_index("ix_classrooms_join_code", "classrooms", ["join_code"])
    op.create_table("memberships",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("classroom_id", sa.Integer(), sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("classroom_id", "user_id"))
    op.create_index("ix_memberships_classroom_id", "memberships", ["classroom_id"])
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    op.create_table("assignments",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("classroom_id", sa.Integer(), sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False), sa.Column("description", sa.Text(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False), sa.Column("status", sa.String(20), nullable=False),
        sa.Column("rubric_json", sa.Text(), nullable=False), sa.Column("answer_key", sa.Text(), nullable=False),
        sa.Column("dataset_json", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_assignments_classroom_id", "assignments", ["classroom_id"])
    op.create_table("submissions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("assignment_id", sa.Integer(), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("draft_markdown", sa.Text(), nullable=False), sa.Column("shared", sa.Boolean(), nullable=False),
        sa.Column("grade_json", sa.Text()), sa.Column("grade_published", sa.Boolean(), nullable=False),
        sa.Column("teacher_comment", sa.Text()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("assignment_id", "student_id"))
    op.create_index("ix_submissions_assignment_id", "submissions", ["assignment_id"])
    op.create_index("ix_submissions_student_id", "submissions", ["student_id"])
    op.create_table("submission_versions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False), sa.Column("body_markdown", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False), sa.Column("review_json", sa.Text()),
        sa.UniqueConstraint("submission_id", "version_number"))
    op.create_index("ix_submission_versions_submission_id", "submission_versions", ["submission_id"])
    op.create_table("ai_jobs",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assignment_id", sa.Integer(), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id", ondelete="CASCADE")),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("submission_versions.id", ondelete="CASCADE")),
        sa.Column("kind", sa.String(24), nullable=False), sa.Column("status", sa.String(20), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False), sa.Column("result_json", sa.Text()), sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    for col in ("owner_id", "assignment_id", "status"):
        op.create_index(f"ix_ai_jobs_{col}", "ai_jobs", [col])
    op.create_table("artifacts",
        sa.Column("id", sa.String(32), primary_key=True), sa.Column("job_id", sa.Integer(), sa.ForeignKey("ai_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("local_path", sa.Text(), nullable=False), sa.Column("display_name", sa.String(240), nullable=False), sa.Column("media_type", sa.String(120), nullable=False))
    op.create_index("ix_artifacts_job_id", "artifacts", ["job_id"])
    op.create_table("comments",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.String(2000), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_comments_submission_id", "comments", ["submission_id"])


def downgrade():
    for table in ("comments", "artifacts", "ai_jobs", "submission_versions", "submissions", "assignments", "memberships", "classrooms", "users"):
        op.drop_table(table)

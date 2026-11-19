"""Scheduled sharing, peer feedback and immutable improvement versions."""
from alembic import op
import sqlalchemy as sa

revision = "0004_peer_learning"
down_revision = "0003_question_max_score"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("assignments", sa.Column("sharing_open_at", sa.DateTime(timezone=True), nullable=True))
    # Keep existing assignments private until students opt in, as before.
    op.add_column("assignments", sa.Column("share_mode", sa.String(20), nullable=False, server_default="opt_in"))
    op.add_column("assignments", sa.Column("allow_improvements", sa.Boolean(), nullable=False, server_default=sa.text("0")))
    op.add_column("submission_versions", sa.Column("is_improvement", sa.Boolean(), nullable=False, server_default=sa.text("0")))
    op.add_column("submission_versions", sa.Column("reflection", sa.Text(), nullable=False, server_default=""))
    op.add_column("submission_versions", sa.Column("grade_json", sa.Text(), nullable=True))
    op.add_column("submission_versions", sa.Column("grade_published", sa.Boolean(), nullable=False, server_default=sa.text("0")))
    op.add_column("submission_versions", sa.Column("teacher_comment", sa.Text(), nullable=True))
    op.execute("""UPDATE submission_versions SET
        grade_json = (SELECT grade_json FROM submissions WHERE submissions.id = submission_versions.submission_id),
        grade_published = (SELECT grade_published FROM submissions WHERE submissions.id = submission_versions.submission_id),
        teacher_comment = (SELECT teacher_comment FROM submissions WHERE submissions.id = submission_versions.submission_id)
        WHERE id IN (SELECT MAX(id) FROM submission_versions GROUP BY submission_id)""")
    op.create_table("peer_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("submission_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("strengths", sa.Text(), nullable=False),
        sa.Column("suggestions", sa.Text(), nullable=False),
        sa.Column("learned", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("version_id", "reviewer_id"))
    op.create_index("ix_peer_reviews_version_id", "peer_reviews", ["version_id"])
    op.create_index("ix_peer_reviews_reviewer_id", "peer_reviews", ["reviewer_id"])


def downgrade():
    op.drop_table("peer_reviews")
    for column in ("teacher_comment", "grade_published", "grade_json", "reflection", "is_improvement"):
        op.drop_column("submission_versions", column)
    for column in ("allow_improvements", "share_mode", "sharing_open_at"):
        op.drop_column("assignments", column)

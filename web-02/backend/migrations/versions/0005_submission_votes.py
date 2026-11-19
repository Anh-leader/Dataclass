"""Class discussion votes, independent of AI comparison and version reviews."""
from alembic import op
import sqlalchemy as sa

revision = "0005_submission_votes"
down_revision = "0004_peer_learning"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("submission_votes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("voter_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submission_id", "voter_id"))
    op.create_index("ix_submission_votes_submission_id", "submission_votes", ["submission_id"])
    op.create_index("ix_submission_votes_voter_id", "submission_votes", ["voter_id"])


def downgrade():
    op.drop_table("submission_votes")

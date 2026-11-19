from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20), default="student")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Classroom(Base):
    __tablename__ = "classrooms"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    join_code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("classroom_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sharing_open_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    share_mode: Mapped[str] = mapped_column(String(20), default="all")
    allow_improvements: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    rubric_json: Mapped[str] = mapped_column(Text, default="[]")
    answer_key: Mapped[str] = mapped_column(Text, default="")
    dataset_json: Mapped[str] = mapped_column(Text, default="[]")
    reference_answer_json: Mapped[str] = mapped_column(Text, default="")
    reference_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AssignmentQuestion(Base):
    __tablename__ = "assignment_questions"
    __table_args__ = (UniqueConstraint("assignment_id", "question_order"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    question_order: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(Text)
    max_score: Mapped[float] = mapped_column(Float, default=10.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    draft_markdown: Mapped[str] = mapped_column(Text, default="")
    shared: Mapped[bool] = mapped_column(Boolean, default=False)
    grade_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    grade_published: Mapped[bool] = mapped_column(Boolean, default=False)
    teacher_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SubmissionAnswer(Base):
    __tablename__ = "submission_answers"
    __table_args__ = (UniqueConstraint("submission_id", "question_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("assignment_questions.id", ondelete="CASCADE"), index=True)
    answer_markdown: Mapped[str] = mapped_column(Text, default="")
    selected_artifacts_json: Mapped[str] = mapped_column(Text, default="[]")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SubmissionVersion(Base):
    __tablename__ = "submission_versions"
    __table_args__ = (UniqueConstraint("submission_id", "version_number"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    body_markdown: Mapped[str] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    review_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    answers_snapshot_json: Mapped[str] = mapped_column(Text, default="[]")
    is_improvement: Mapped[bool] = mapped_column(Boolean, default=False)
    reflection: Mapped[str] = mapped_column(Text, default="")
    grade_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    grade_published: Mapped[bool] = mapped_column(Boolean, default=False)
    teacher_comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class AIJob(Base):
    __tablename__ = "ai_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    submission_id: Mapped[int | None] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=True)
    version_id: Mapped[int | None] = mapped_column(ForeignKey("submission_versions.id", ondelete="CASCADE"), nullable=True)
    question_id: Mapped[int | None] = mapped_column(ForeignKey("assignment_questions.id", ondelete="CASCADE"), nullable=True)
    kind: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    prompt: Mapped[str] = mapped_column(Text, default="")
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Artifact(Base):
    __tablename__ = "artifacts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("ai_jobs.id", ondelete="CASCADE"), index=True)
    local_path: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(String(240))
    media_type: Mapped[str] = mapped_column(String(120))


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PeerReview(Base):
    __tablename__ = "peer_reviews"
    __table_args__ = (UniqueConstraint("version_id", "reviewer_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("submission_versions.id", ondelete="CASCADE"), index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    strengths: Mapped[str] = mapped_column(Text)
    suggestions: Mapped[str] = mapped_column(Text)
    learned: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SubmissionVote(Base):
    __tablename__ = "submission_votes"
    __table_args__ = (UniqueConstraint("submission_id", "voter_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), index=True)
    voter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

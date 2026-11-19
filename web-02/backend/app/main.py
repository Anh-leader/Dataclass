from __future__ import annotations

import json
import math
import re
import secrets
import time
import zipfile
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import ALLOWED_SUFFIXES, ARTIFACT_DIR, COOKIE_SECURE, MAX_ASSIGNMENT_BYTES, MAX_FILE_BYTES, UPLOAD_DIR, SECRET_KEY
from .database import engine, get_db
from .models import AIJob, Artifact, Assignment, AssignmentQuestion, Classroom, Comment, Membership, PeerReview, Submission, SubmissionAnswer, SubmissionVersion, SubmissionVote, User, utcnow
from .security import hash_password, verify_password
from .peer_comparison import build_comparison_context, comparison_sources, validate_saved_comparison


app = FastAPI(title="DataClass API", version="1.0.0")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, session_cookie="web02_session", max_age=60 * 60 * 12, same_site="lax", https_only=COOKIE_SECURE)
_rate_events: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(key: str, limit: int, seconds: int = 60):
    now = time.monotonic()
    events = _rate_events[key]
    while events and now - events[0] > seconds:
        events.popleft()
    if len(events) >= limit:
        raise HTTPException(429, "Bạn thao tác quá nhanh. Vui lòng đợi một chút rồi thử lại.")
    events.append(now)


@app.on_event("startup")
def startup():
    if __import__("os").getenv("WEB02_ENV") == "production":
        if SECRET_KEY == "change-this-secret-before-deployment" or not COOKIE_SECURE:
            raise RuntimeError("Set WEB02_SECRET_KEY and WEB02_COOKIE_SECURE=true for production.")
    with engine.connect() as connection:
        if not engine.dialect.has_table(connection, "users"):
            raise RuntimeError("Database is not initialized. Run `alembic upgrade head` first.")


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    user = db.get(User, user_id) if user_id else None
    if not user:
        raise HTTPException(401, "Vui lòng đăng nhập.")
    return user


def require_csrf(request: Request):
    expected = request.session.get("csrf")
    supplied = request.headers.get("x-csrf-token", "")
    if not expected or not secrets.compare_digest(str(expected), supplied):
        raise HTTPException(403, "CSRF token không hợp lệ.")


def teacher_only(user: User):
    if user.role != "teacher":
        raise HTTPException(403, "Chức năng này dành cho giáo viên.")


def parse_dt(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        raise HTTPException(422, "Thời hạn không hợp lệ; gửi thời gian ISO 8601 có múi giờ.")
    if dt.tzinfo is None:
        raise HTTPException(422, "Thời hạn phải có múi giờ.")
    return dt.astimezone(timezone.utc)


def utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def json_load(value: str | None, fallback):
    try:
        return json.loads(value) if value else fallback
    except (TypeError, json.JSONDecodeError):
        return fallback


QUESTION_ORDERS = tuple(range(1, 21))


def ordered_questions(db: Session, assignment: Assignment) -> list[AssignmentQuestion]:
    return db.scalars(select(AssignmentQuestion).where(AssignmentQuestion.assignment_id == assignment.id).order_by(AssignmentQuestion.question_order)).all()


def question_view(q: AssignmentQuestion) -> dict:
    return {"id": q.id, "assignment_id": q.assignment_id, "question_order": q.question_order,
            "question_text": q.question_text, "max_score": float(q.max_score)}


def normalize_questions(payload: dict) -> list[dict]:
    """Validate a complete assignment containing 1 to 20 questions."""
    cleaned = normalize_question_items(payload)
    if [item["question_order"] for item in cleaned] != list(range(1, len(cleaned) + 1)):
        raise HTTPException(422, "Câu hỏi phải được đánh số liên tiếp từ 1.")
    return cleaned


def normalize_question_items(payload: dict) -> list[dict]:
    """Validate individual question items used for draft editing."""
    raw = payload.get("questions")
    if not isinstance(raw, list) or not 1 <= len(raw) <= 20:
        raise HTTPException(422, "Bài tập cần từ 1 đến 20 câu hỏi.")
    seen = set()
    cleaned = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise HTTPException(422, "Dữ liệu câu hỏi không hợp lệ.")
        order = item.get("question_order")
        try:
            order = int(order)
        except (TypeError, ValueError):
            raise HTTPException(422, "Thứ tự câu hỏi phải là số.")
        if order not in QUESTION_ORDERS:
            raise HTTPException(422, "Thứ tự câu hỏi phải nằm trong khoảng 1 đến 20.")
        if order in seen:
            raise HTTPException(422, f"Trùng thứ tự câu hỏi: Câu hỏi {order} bị lặp lại.")
        seen.add(order)
        text = str(item.get("question_text", "")).strip()
        if not text:
            raise HTTPException(422, f"Câu hỏi {order} đang trống. Vui lòng nhập nội dung câu hỏi.")
        if len(text) > 8000:
            raise HTTPException(422, f"Câu hỏi {order} vượt 8.000 ký tự.")
        try:
            max_score = float(item.get("max_score", 10.0))
        except (TypeError, ValueError):
            raise HTTPException(422, f"Điểm tối đa của Câu hỏi {order} phải là số.")
        if not math.isfinite(max_score) or max_score <= 0 or max_score > 100:
            raise HTTPException(422, f"Điểm tối đa của Câu hỏi {order} phải lớn hơn 0 và không quá 100.")
        cleaned.append({"question_order": order, "question_text": text, "max_score": max_score})
    cleaned.sort(key=lambda x: x["question_order"])
    return cleaned


def sync_questions(db: Session, assignment: Assignment, payload: dict) -> list[AssignmentQuestion]:
    """Create or replace questions of an assignment (teacher only).

    Allowed while the assignment is a draft, or while a published assignment
    still has no questions yet (legacy data migrated without questions).
    Once a published assignment already has questions, they are locked so
    existing submissions keep referring to a stable set of questions.
    """
    if assignment.status == "published" and ordered_questions(db, assignment):
        raise HTTPException(409, "Không thể sửa câu hỏi sau khi bài đã công bố và có câu hỏi.")
    cleaned = normalize_question_items(payload)
    existing = {q.question_order: q for q in ordered_questions(db, assignment)}
    for item in cleaned:
        question = existing.get(item["question_order"])
        if question:
            question.question_text = item["question_text"]
            question.max_score = item["max_score"]
        else:
            db.add(AssignmentQuestion(assignment_id=assignment.id, question_order=item["question_order"],
                                      question_text=item["question_text"], max_score=item["max_score"]))
    for order, question in existing.items():
        if all(item["question_order"] != order for item in cleaned):
            db.delete(question)
    db.flush()
    return ordered_questions(db, assignment)


def ensure_assignment_questions(db: Session, assignment: Assignment) -> list[AssignmentQuestion]:
    questions = ordered_questions(db, assignment)
    if not questions or len(questions) > 20 or [q.question_order for q in questions] != list(range(1, len(questions) + 1)):
        raise HTTPException(422, "Bài tập cần từ 1 đến 20 câu hỏi được đánh số liên tiếp trước khi công bố.")
    return questions


def ensure_submission_answers(db: Session, submission: Submission, assignment: Assignment, questions: list[AssignmentQuestion]):
    """Require a non-empty answer for every assignment question before submitting."""
    if not questions:
        raise HTTPException(422, "Bài tập chưa có câu hỏi.")
    answers = db.scalars(select(SubmissionAnswer).where(SubmissionAnswer.submission_id == submission.id)).all()
    by_question = {a.question_id: a for a in answers}
    for question in questions:
        answer = by_question.get(question.id)
        if not answer or not answer.answer_markdown.strip():
            raise HTTPException(422, f"Bạn chưa trả lời Câu hỏi {question.question_order}.")
    return answers


def allowed_artifact_ids(db: Session, submission: Submission, assignment: Assignment) -> set[str]:
    """Artifact ids generated for this student on this assignment."""
    job_ids = db.scalars(select(AIJob.id).where(AIJob.owner_id == submission.student_id, AIJob.assignment_id == assignment.id)).all()
    allowed = set()
    for job_id in job_ids:
        for artifact in db.scalars(select(Artifact).where(Artifact.job_id == job_id)).all():
            allowed.add(artifact.id)
    return allowed


def answer_view(answer: SubmissionAnswer, artifacts_by_id: dict[str, Artifact]) -> dict:
    artifact_ids = json_load(answer.selected_artifacts_json, [])
    artifacts = []
    for artifact_id in artifact_ids:
        artifact = artifacts_by_id.get(str(artifact_id))
        if artifact:
            artifacts.append({"id": artifact.id, "name": artifact.display_name, "media_type": artifact.media_type, "url": f"/api/assets/{artifact.id}"})
    return {"question_id": answer.question_id, "answer_markdown": answer.answer_markdown,
            "artifacts": artifacts, "updated_at": utc(answer.updated_at).isoformat()}


def reference_view(assignment: Assignment, include_private: bool) -> dict | None:
    data = json_load(assignment.reference_answer_json, {}) if include_private else None
    published = bool(assignment.reference_published)
    if include_private:
        return {"published": published, "answers": data.get("answers", []), "artifacts": data.get("artifacts", []), "note": data.get("note", "")}
    return {"published": published}


def current_assignment(db: Session, assignment_id: int) -> Assignment:
    item = db.get(Assignment, assignment_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy bài tập.")
    return item


def can_access_class(db: Session, classroom_id: int, user: User) -> Classroom:
    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(404, "Không tìm thấy lớp.")
    if classroom.owner_id != user.id and not db.scalar(select(Membership.id).where(Membership.classroom_id == classroom_id, Membership.user_id == user.id)):
        raise HTTPException(403, "Bạn không thuộc lớp này.")
    return classroom


def can_access_assignment(db: Session, assignment: Assignment, user: User):
    classroom = db.get(Classroom, assignment.classroom_id)
    if not classroom:
        raise HTTPException(404, "Không tìm thấy lớp của bài tập.")
    if classroom.owner_id != user.id and not db.scalar(select(Membership.id).where(Membership.classroom_id == classroom.id, Membership.user_id == user.id)):
        raise HTTPException(403, "Bạn không thuộc lớp này.")
    if assignment.status != "published" and classroom.owner_id != user.id:
        raise HTTPException(404, "Không tìm thấy bài tập.")
    return classroom


def get_or_create_submission(db: Session, assignment_id: int, user_id: int) -> Submission:
    item = db.scalar(select(Submission).where(Submission.assignment_id == assignment_id, Submission.student_id == user_id))
    if item:
        return item
    item = Submission(assignment_id=assignment_id, student_id=user_id)
    db.add(item)
    db.flush()
    return item


def dataset_items(assignment: Assignment) -> list[dict]:
    return json_load(assignment.dataset_json, [])


def sharing_time(assignment: Assignment) -> datetime:
    return utc(assignment.sharing_open_at or assignment.due_at)


def sharing_open(assignment: Assignment) -> bool:
    return assignment.status == "published" and sharing_time(assignment) <= utcnow()


def latest_version(db: Session, submission: Submission) -> SubmissionVersion | None:
    return db.scalar(select(SubmissionVersion).where(SubmissionVersion.submission_id == submission.id).order_by(SubmissionVersion.version_number.desc()))


def can_improve(db: Session, assignment: Assignment, user: User) -> bool:
    if not assignment.allow_improvements or not sharing_open(assignment):
        return False
    submission = db.scalar(select(Submission).where(Submission.assignment_id == assignment.id, Submission.student_id == user.id))
    return bool(submission and latest_version(db, submission))


def require_work_access(db: Session, assignment: Assignment, user: User):
    can_access_assignment(db, assignment, user)
    if user.role != "student" or assignment.status != "published":
        raise HTTPException(403, "Chỉ sinh viên trong lớp có thể làm bài.")
    if utc(assignment.due_at) <= utcnow() and not can_improve(db, assignment, user):
        raise HTTPException(409, "Đã hết hạn nộp. Bản cải thiện chỉ được mở cho sinh viên đã nộp khi giáo viên cho phép và đến giờ chia sẻ.")


def visible_submission(db: Session, submission: Submission, user: User) -> Assignment:
    assignment = current_assignment(db, submission.assignment_id)
    can_access_assignment(db, assignment, user)
    if not sharing_open(assignment) or (assignment.share_mode == "opt_in" and not submission.shared) or not latest_version(db, submission):
        raise HTTPException(404, "Bài chưa được mở chia sẻ.")
    return assignment


def version_markdown(version: SubmissionVersion) -> str:
    body = version.body_markdown
    # Include selected evidence even if a legacy version did not embed its links.
    for answer in json_load(version.answers_snapshot_json, []):
        for artifact in answer.get("artifacts", []):
            link = f"/api/assets/{artifact['id']}"
            if link not in body:
                label = "![Biểu đồ]" if artifact.get("media_type", "").startswith("image/") else "[Tải bằng chứng]"
                body += f"\n\n{label}({link})"
    return body


def peer_review_view(db: Session, item: PeerReview, user: User) -> dict:
    return {"id": item.id, "version_id": item.version_id, "reviewer_id": item.reviewer_id,
            "reviewer": db.get(User, item.reviewer_id).full_name, "rating": item.rating,
            "strengths": item.strengths, "suggestions": item.suggestions, "learned": item.learned,
            "is_mine": item.reviewer_id == user.id, "updated_at": utc(item.updated_at).isoformat()}


def assignment_policy(payload: dict, due_at: datetime, current: Assignment | None = None) -> dict:
    opening = payload.get("sharing_open_at", sharing_time(current).isoformat() if current else due_at.isoformat())
    mode = payload.get("share_mode", current.share_mode if current else "all")
    improvements = payload.get("allow_improvements", current.allow_improvements if current else True)
    if not isinstance(mode, str) or mode not in {"all", "opt_in"} or not isinstance(improvements, bool):
        raise HTTPException(422, "Cấu hình chia sẻ hoặc cải thiện bài không hợp lệ.")
    return {"sharing_open_at": parse_dt(opening), "share_mode": mode, "allow_improvements": improvements}


def payload_version_id(payload: dict) -> int:
    value = payload.get("version_id")
    if type(value) is not int or value <= 0:
        raise HTTPException(422, "Mã phiên bản bài nộp không hợp lệ.")
    return value


def answer_views(db: Session, answers: list[SubmissionAnswer]) -> list[dict]:
    artifact_ids = []
    for answer in answers:
        artifact_ids.extend(json_load(answer.selected_artifacts_json, []))
    artifacts = {art.id: art for art in db.scalars(select(Artifact).where(Artifact.id.in_(artifact_ids))).all()} if artifact_ids else {}
    result = []
    for answer in sorted(answers, key=lambda a: a.question_id):
        result.append(answer_view(answer, artifacts))
    return result


def assignment_view(db: Session, assignment: Assignment, user: User) -> dict:
    classroom = db.get(Classroom, assignment.classroom_id)
    student_view = classroom.owner_id != user.id
    rubric = json_load(assignment.rubric_json, [])
    if student_view:
        rubric = [{k: v for k, v in item.items() if k != "hint"} for item in rubric]
    questions = [question_view(q) for q in ordered_questions(db, assignment)]
    result = {
        "id": assignment.id, "classroom_id": assignment.classroom_id, "classroom_name": classroom.name,
        "title": assignment.title, "description": assignment.description, "due_at": utc(assignment.due_at).isoformat(),
        "status": assignment.status, "rubric": rubric,
        "sharing_open_at": sharing_time(assignment).isoformat(), "sharing_open": sharing_open(assignment),
        "share_mode": assignment.share_mode, "allow_improvements": assignment.allow_improvements,
        "can_edit": user.role == "student" and (utc(assignment.due_at) > utcnow() or can_improve(db, assignment, user)),
        "questions": questions,
        "datasets": [{"id": item["id"], "name": item["name"], "size": item["size"]} for item in dataset_items(assignment)],
        "is_teacher": not student_view,
    }
    if not student_view:
        result["answer_key"] = assignment.answer_key
        result["reference"] = reference_view(assignment, include_private=True)
        generation = db.scalar(select(AIJob).where(AIJob.assignment_id == assignment.id, AIJob.kind == "exam_generation").order_by(AIJob.id.desc()))
        result["generation_job"] = {"id": generation.id, "status": generation.status} if generation else None
    else:
        submission = db.scalar(select(Submission).where(Submission.assignment_id == assignment.id, Submission.student_id == user.id))
        if submission:
            versions = db.scalars(select(SubmissionVersion).where(SubmissionVersion.submission_id == submission.id).order_by(SubmissionVersion.version_number.desc())).all()
            answers = db.scalars(select(SubmissionAnswer).where(SubmissionAnswer.submission_id == submission.id)).all()
            result["submission"] = submission_view(submission, versions, include_private=submission.student_id == user.id, answers=answer_views(db, answers), db=db)
    return result


def submission_view(submission: Submission, versions: list[SubmissionVersion], include_private=True, answers: list[dict] | None = None, db: Session | None = None) -> dict:
    def version_view(version):
        job = db.scalar(select(AIJob).where(AIJob.version_id == version.id, AIJob.kind == "submitted_review").order_by(AIJob.id.desc())) if db is not None else None
        review = json_load(version.review_json, None)
        return {"id": version.id, "version_number": version.version_number, "body_markdown": version_markdown(version),
                "submitted_at": utc(version.submitted_at).isoformat(), "review": review,
                "review_status": job.status if job else ("done" if review else "none"), "review_job_id": job.id if job else None,
                "is_improvement": version.is_improvement, "reflection": version.reflection,
                "grade": json_load(version.grade_json, None) if version.grade_published or not include_private else None,
                "grade_published": version.grade_published,
                "teacher_comment": version.teacher_comment if version.grade_published or not include_private else None,
                "peer_reviews": [{"id": p.id, "reviewer": db.get(User, p.reviewer_id).full_name, "rating": p.rating,
                                  "strengths": p.strengths, "suggestions": p.suggestions, "learned": p.learned}
                                 for p in db.scalars(select(PeerReview).where(PeerReview.version_id == version.id)).all()] if db is not None else [],
                "answers_snapshot": json_load(version.answers_snapshot_json, [])}
    return {
        "id": submission.id, "draft_markdown": submission.draft_markdown, "shared": submission.shared,
        "grade": json_load(submission.grade_json, None) if submission.grade_published or not include_private else None,
        "grade_published": submission.grade_published,
        "teacher_comment": submission.teacher_comment if submission.grade_published or not include_private else None,
        "answers": answers if answers is not None else [],
        "versions": [version_view(v) for v in versions],
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/auth/csrf")
def csrf_token(request: Request):
    request.session.setdefault("csrf", secrets.token_urlsafe(32))
    return {"csrf_token": request.session["csrf"]}


@app.post("/api/auth/register")
def register(payload: dict, request: Request, db: Session = Depends(get_db), _: None = Depends(require_csrf)):
    rate_limit(f"register:{request.client.host if request.client else 'unknown'}", 30)
    email = str(payload.get("email", "")).strip().lower()
    name = str(payload.get("full_name", "")).strip()
    password = str(payload.get("password", ""))
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254:
        raise HTTPException(422, "Email không hợp lệ.")
    if len(name) < 2 or len(name) > 120 or len(password) < 10 or len(password) > 128:
        raise HTTPException(422, "Tên cần từ 2 ký tự; mật khẩu cần từ 10 đến 128 ký tự.")
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(409, "Email đã được sử dụng.")
    role = str(payload.get("role", "student")).strip().lower()
    if role not in {"student", "teacher"}:
        role = "student"
    user = User(email=email, full_name=name, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["csrf"] = secrets.token_urlsafe(32)
    return {"user": user_view(user), "csrf_token": request.session["csrf"]}


def user_view(user: User) -> dict:
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}


@app.post("/api/auth/login")
def login(payload: dict, request: Request, db: Session = Depends(get_db), _: None = Depends(require_csrf)):
    email = str(payload.get("email", "")).strip().lower()
    rate_limit(f"login:{email}", 10)
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(str(payload.get("password", "")), user.password_hash):
        raise HTTPException(401, "Email hoặc mật khẩu chưa đúng.")
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["csrf"] = secrets.token_urlsafe(32)
    return {"user": user_view(user), "csrf_token": request.session["csrf"]}


@app.post("/api/auth/logout")
def logout(request: Request, _: None = Depends(require_csrf)):
    request.session.clear()
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: User = Depends(require_user)):
    return {"user": user_view(user)}


@app.get("/api/classes")
def list_classes(db: Session = Depends(get_db), user: User = Depends(require_user)):
    if user.role == "teacher":
        classes = db.scalars(select(Classroom).where(Classroom.owner_id == user.id).order_by(Classroom.created_at.desc())).all()
    else:
        classes = db.scalars(select(Classroom).join(Membership).where(Membership.user_id == user.id).order_by(Classroom.created_at.desc())).all()
    result = []
    for item in classes:
        assignments = db.scalars(select(Assignment).where(Assignment.classroom_id == item.id, Assignment.status == "published")).all()
        result.append({"id": item.id, "name": item.name, "join_code": item.join_code if user.role == "teacher" else None,
                       "assignment_count": len(assignments), "teacher_name": db.get(User, item.owner_id).full_name})
    return result


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(require_user)):
    if user.role == "teacher":
        classes = db.scalars(select(Classroom).where(Classroom.owner_id == user.id)).all()
        class_ids = [c.id for c in classes]
    else:
        class_ids = db.scalars(select(Membership.classroom_id).where(Membership.user_id == user.id)).all()
        classes = db.scalars(select(Classroom).where(Classroom.id.in_(class_ids))).all() if class_ids else []

    assignments = []
    if class_ids:
        assignments = db.scalars(select(Assignment).where(Assignment.classroom_id.in_(class_ids))).all()
    published = [a for a in assignments if a.status == "published"]
    open_assignments = [a for a in published if utc(a.due_at) > utcnow()]

    # Per-class statistics.
    total_students = 0
    recent_classes = []
    for c in classes:
        student_count = len(db.scalars(select(Membership.id).where(Membership.classroom_id == c.id)).all())
        total_students += student_count
        class_assignments = db.scalars(select(Assignment).where(Assignment.classroom_id == c.id, Assignment.status == "published")).all()
        recent_classes.append({"id": c.id, "name": c.name, "join_code": c.join_code if user.role == "teacher" else None,
                               "student_count": student_count, "assignment_count": len(class_assignments)})

    if user.role == "teacher":
        pending_grades = 0
        if assignments:
            assignment_ids = [a.id for a in assignments]
            for s in db.scalars(select(Submission).where(Submission.assignment_id.in_(assignment_ids))).all():
                has_version = db.scalar(select(SubmissionVersion.id).where(SubmissionVersion.submission_id == s.id))
                if has_version and (not s.grade_published or not s.grade_json):
                    pending_grades += 1
        return {"role": "teacher", "class_count": len(classes), "open_assignments": len(open_assignments),
                "pending_grades": pending_grades, "total_students": total_students, "recent_classes": recent_classes}

    my_submissions = 0
    if assignments:
        my_submissions = len(db.scalars(select(Submission).where(
            Submission.student_id == user.id,
            Submission.assignment_id.in_([a.id for a in assignments]))).all())
    return {"role": "student", "class_count": len(classes), "open_assignments": len(open_assignments),
            "my_submissions": my_submissions, "total_students": total_students, "recent_classes": recent_classes}


@app.post("/api/classes")
def create_class(payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    teacher_only(user)
    name = str(payload.get("name", "")).strip()
    if not name or len(name) > 160:
        raise HTTPException(422, "Tên lớp cần từ 1 đến 160 ký tự.")
    code = secrets.token_urlsafe(7).replace("-", "").replace("_", "")[:10].upper()
    item = Classroom(name=name, join_code=code, owner_id=user.id)
    db.add(item)
    db.commit()
    return {"id": item.id, "name": item.name, "join_code": item.join_code}


@app.post("/api/classes/join")
def join_class(payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    if user.role != "student":
        raise HTTPException(403, "Chỉ sinh viên tham gia lớp bằng mã.")
    code = str(payload.get("code", "")).strip().upper()
    classroom = db.scalar(select(Classroom).where(Classroom.join_code == code))
    if not classroom:
        raise HTTPException(404, "Mã lớp không hợp lệ.")
    if not db.scalar(select(Membership.id).where(Membership.classroom_id == classroom.id, Membership.user_id == user.id)):
        db.add(Membership(classroom_id=classroom.id, user_id=user.id))
        db.commit()
    return {"id": classroom.id, "name": classroom.name}


@app.get("/api/classes/{class_id}")
def get_class(class_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    classroom = can_access_class(db, class_id, user)
    items = db.scalars(select(Assignment).where(Assignment.classroom_id == class_id).order_by(Assignment.due_at)).all()
    if user.role != "teacher":
        items = [item for item in items if item.status == "published"]
    return {"id": classroom.id, "name": classroom.name, "join_code": classroom.join_code if classroom.owner_id == user.id else None,
            "assignments": [assignment_view(db, item, user) for item in items]}


@app.get("/api/assignments/{assignment_id}")
def get_assignment(assignment_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    return assignment_view(db, assignment, user)


@app.post("/api/classes/{class_id}/assignments")
def create_assignment(class_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    teacher_only(user)
    can_access_class(db, class_id, user)
    title = str(payload.get("title", "")).strip()
    rubric = payload.get("rubric", [])
    if not title or len(title) > 200 or not isinstance(rubric, list):
        raise HTTPException(422, "Tiêu đề hoặc rubric không hợp lệ.")
    cleaned = []
    for i, item in enumerate(rubric):
        try:
            points = float(item.get("max_points", 0))
        except (AttributeError, ValueError, TypeError):
            raise HTTPException(422, "Điểm tối đa của tiêu chí phải là số.")
        if not math.isfinite(points) or points <= 0:
            raise HTTPException(422, "Mỗi tiêu chí cần điểm tối đa lớn hơn 0.")
        cleaned.append({"id": str(item.get("id") or uuid4().hex[:8]), "title": str(item.get("title", f"Tiêu chí {i + 1}"))[:160],
                        "description": str(item.get("description", ""))[:1200], "max_points": points, "hint": str(item.get("hint", ""))[:800]})
    if cleaned and round(sum(x["max_points"] for x in cleaned), 2) != 10:
        raise HTTPException(422, "Tổng điểm tối đa của rubric phải bằng 10.")
    due_at = parse_dt(payload.get("due_at"))
    if due_at <= utcnow():
        raise HTTPException(422, "Hạn nộp phải nằm trong tương lai.")
    cleaned_questions = [] if payload.get("ai_generate") is True and not payload.get("questions") else normalize_questions(payload)
    assignment = Assignment(classroom_id=class_id, title=title, description=str(payload.get("description", ""))[:12000],
                           due_at=due_at, rubric_json=json.dumps(cleaned, ensure_ascii=False),
                           answer_key=str(payload.get("answer_key", ""))[:20000], **assignment_policy(payload, due_at))
    db.add(assignment)
    db.flush()
    for item in cleaned_questions:
        db.add(AssignmentQuestion(assignment_id=assignment.id, question_order=item["question_order"],
                                  question_text=item["question_text"], max_score=item["max_score"]))
    db.commit()
    return assignment_view(db, assignment, user)


@app.put("/api/assignments/{assignment_id}/settings")
def update_assignment_settings(assignment_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    classroom = can_access_assignment(db, assignment, user)
    if classroom.owner_id != user.id:
        raise HTTPException(403, "Chỉ giáo viên của lớp có thể thay đổi lịch bài tập.")
    due_at = parse_dt(payload["due_at"]) if "due_at" in payload else utc(assignment.due_at)
    if due_at != utc(assignment.due_at) and due_at <= utcnow():
        raise HTTPException(422, "Hạn nộp mới phải nằm trong tương lai.")
    policy = assignment_policy(payload, due_at, assignment)
    assignment.due_at = due_at
    for key, value in policy.items():
        setattr(assignment, key, value)
    db.commit()
    return assignment_view(db, assignment, user)


@app.put("/api/assignments/{assignment_id}/questions")
def update_questions(assignment_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    teacher_only(user)
    questions = sync_questions(db, assignment, payload)
    db.commit()
    return {"questions": [question_view(q) for q in questions]}


@app.put("/api/assignments/{assignment_id}/reference")
def save_reference(assignment_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    teacher_only(user)
    questions = ordered_questions(db, assignment)
    question_by_id = {q.id: q for q in questions}
    raw_answers = payload.get("answers")
    if not questions or not isinstance(raw_answers, list) or len(raw_answers) != len(questions):
        raise HTTPException(422, "Bài tham khảo phải trả lời đầy đủ các câu hỏi.")
    answers = []
    seen = set()
    for item in raw_answers:
        if not isinstance(item, dict):
            raise HTTPException(422, "Dữ liệu bài tham khảo không hợp lệ.")
        question = question_by_id.get(item.get("question_id"))
        if not question:
            raise HTTPException(422, "Câu hỏi không thuộc bài tập này.")
        if question.id in seen:
            raise HTTPException(422, "Trùng câu hỏi trong bài tham khảo.")
        seen.add(question.id)
        text = str(item.get("answer_markdown", "")).strip()
        if not text:
            raise HTTPException(422, f"Bài tham khảo đang thiếu nội dung Câu hỏi {question.question_order}.")
        artifact_ids = item.get("artifact_ids")
        if not isinstance(artifact_ids, list):
            artifact_ids = []
        answers.append({"question_id": question.id, "question_order": question.question_order, "answer_markdown": text[:20000], "artifact_ids": [str(a) for a in artifact_ids][:20]})
    data = json_load(assignment.reference_answer_json, {}) if assignment.reference_answer_json else {}
    data["answers"] = answers
    data["artifacts"] = payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else data.get("artifacts", [])
    data["note"] = str(payload.get("note", ""))[:8000]
    assignment.reference_answer_json = json.dumps(data, ensure_ascii=False)
    db.commit()
    return {"reference": reference_view(assignment, include_private=True)}


@app.post("/api/assignments/{assignment_id}/reference/publish")
def publish_reference(assignment_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    teacher_only(user)
    publish = bool(payload.get("published", True))
    if publish:
        data = json_load(assignment.reference_answer_json, {})
        answers = data.get("answers", [])
        if not answers or len(answers) != len(ordered_questions(db, assignment)) or any(not str(a.get("answer_markdown", "")).strip() for a in answers):
            raise HTTPException(422, "Chưa thể công bố: bài tham khảo phải trả lời đầy đủ các câu hỏi.")
    assignment.reference_published = publish
    db.commit()
    return {"reference": reference_view(assignment, include_private=True)}


@app.get("/api/assignments/{assignment_id}/reference")
def get_reference(assignment_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    assignment = current_assignment(db, assignment_id)
    classroom = can_access_assignment(db, assignment, user)
    if classroom.owner_id == user.id:
        return {"reference": reference_view(assignment, include_private=True), "can_view": True}
    if not assignment.reference_published:
        raise HTTPException(404, "Giảng viên chưa công bố bài tham khảo.")
    submission = db.scalar(select(Submission).where(Submission.assignment_id == assignment.id, Submission.student_id == user.id))
    has_submitted = submission and db.scalar(select(SubmissionVersion.id).where(SubmissionVersion.submission_id == submission.id))
    if not has_submitted:
        raise HTTPException(403, "Bạn cần nộp bài lần đầu trước khi xem bài tham khảo.")
    return {"reference": reference_view(assignment, include_private=True), "can_view": True}


@app.post("/api/assignments/{assignment_id}/datasets")
async def upload_datasets(assignment_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    teacher_only(user)
    if assignment.status != "draft":
        raise HTTPException(409, "Dataset đã được cố định sau khi công bố.")
    directory = UPLOAD_DIR / f"assignment-{assignment.id}"
    directory.mkdir(parents=True, exist_ok=True)
    existing = dataset_items(assignment)
    if len(existing) + len(files) > 3:
        raise HTTPException(422, "Mỗi bài tập hỗ trợ tối đa 3 dataset.")
    total = sum(item.get("size", 0) for item in existing)
    added = []
    new_paths: list[Path] = []
    try:
        for upload in files:
            suffix = Path(upload.filename or "").suffix.lower()
            if suffix not in ALLOWED_SUFFIXES:
                raise HTTPException(415, "Chỉ nhận CSV và XLSX.")
            safe_name = re.sub(r"[^\w.() -]", "_", Path(upload.filename or "dataset").name)[:180]
            target = directory / f"{uuid4().hex}-{safe_name}"
            new_paths.append(target)
            size = 0
            with target.open("wb") as output:
                while chunk := await upload.read(1024 * 1024):
                    size += len(chunk)
                    total += len(chunk)
                    if size > MAX_FILE_BYTES or total > MAX_ASSIGNMENT_BYTES:
                        raise HTTPException(413, "Tệp vượt giới hạn 10 MB hoặc tổng dataset vượt 20 MB.")
                    output.write(chunk)
            if not size:
                target.unlink(missing_ok=True)
                raise HTTPException(422, "Tệp rỗng.")
            try:
                if suffix == ".csv":
                    pd.read_csv(target, nrows=10, low_memory=False)
                else:
                    with zipfile.ZipFile(target) as archive:
                        members = archive.infolist()
                        expanded = sum(member.file_size for member in members)
                        compressed = sum(max(member.compress_size, 1) for member in members)
                        if expanded > 100 * 1024 * 1024 or expanded / compressed > 100:
                            raise ValueError("Workbook có kích thước giải nén bất thường.")
                    with pd.ExcelFile(target):
                        pass
            except Exception as exc:
                target.unlink(missing_ok=True)
                raise HTTPException(422, f"Không đọc được {safe_name}: {exc}")
            added.append({"id": uuid4().hex, "name": safe_name, "size": size, "path": str(target.resolve())})
    except Exception:
        for path in new_paths:
            path.unlink(missing_ok=True)
        raise
    assignment.dataset_json = json.dumps(existing + added, ensure_ascii=False)
    db.commit()
    return {"datasets": [{"id": x["id"], "name": x["name"], "size": x["size"]} for x in existing + added]}


@app.delete("/api/assignments/{assignment_id}/datasets/{dataset_id}")
def delete_dataset(assignment_id: int, dataset_id: str, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    teacher_only(user)
    if assignment.status != "draft":
        raise HTTPException(409, "Dataset đã được cố định sau khi công bố.")
    items = dataset_items(assignment)
    found = next((x for x in items if x["id"] == dataset_id), None)
    if not found:
        raise HTTPException(404, "Không tìm thấy dataset.")
    Path(found["path"]).unlink(missing_ok=True)
    assignment.dataset_json = json.dumps([x for x in items if x["id"] != dataset_id])
    db.commit()
    return {"ok": True}


@app.post("/api/assignments/{assignment_id}/publish")
def publish_assignment(assignment_id: int, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    teacher_only(user)
    if not dataset_items(assignment):
        raise HTTPException(422, "Cần ít nhất một dataset trước khi công bố.")
    ensure_assignment_questions(db, assignment)
    if utc(assignment.due_at) <= utcnow():
        raise HTTPException(422, "Hạn nộp phải nằm trong tương lai.")
    assignment.status = "published"
    db.commit()
    return assignment_view(db, assignment, user)


@app.get("/api/assignments/{assignment_id}/datasets/{dataset_id}/preview")
def preview_dataset(assignment_id: int, dataset_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    item = next((x for x in dataset_items(assignment) if x["id"] == dataset_id), None)
    if not item:
        raise HTTPException(404, "Không tìm thấy dataset.")
    path = Path(item["path"]).resolve()
    if not path.is_file() or not path.is_relative_to(UPLOAD_DIR.resolve()):
        raise HTTPException(404, "Dataset không còn khả dụng.")
    try:
        frame = pd.read_csv(path, nrows=20, low_memory=False) if path.suffix.lower() == ".csv" else pd.read_excel(path, nrows=20)
    except Exception as exc:
        raise HTTPException(422, f"Không thể xem trước dataset: {exc}")
    rows = frame.astype(object).where(frame.notna(), None).to_dict(orient="records")
    return {"columns": list(frame.columns), "rows": rows, "row_count_shown": len(rows)}


@app.put("/api/assignments/{assignment_id}/draft")
def save_draft(assignment_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    require_work_access(db, assignment, user)
    body = str(payload.get("body_markdown", ""))
    if len(body) > 100_000:
        raise HTTPException(413, "Báo cáo vượt 100.000 ký tự.")
    submission = get_or_create_submission(db, assignment.id, user.id)
    submission.draft_markdown = body
    db.commit()
    return {"submission_id": submission.id, "updated_at": utc(submission.updated_at).isoformat()}


@app.put("/api/assignments/{assignment_id}/answers")
def save_answers(assignment_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    require_work_access(db, assignment, user)
    questions = ordered_questions(db, assignment)
    question_by_id = {q.id: q for q in questions}
    items = payload.get("answers")
    if not isinstance(items, list):
        raise HTTPException(422, "Dữ liệu câu trả lời không hợp lệ.")
    submission = get_or_create_submission(db, assignment.id, user.id)
    allowed_artifacts = allowed_artifact_ids(db, submission, assignment)
    for item in items:
        if not isinstance(item, dict):
            raise HTTPException(422, "Dữ liệu câu trả lời không hợp lệ.")
        question = question_by_id.get(item.get("question_id"))
        if not question:
            raise HTTPException(422, "Câu hỏi không thuộc bài tập này.")
        answer_markdown = str(item.get("answer_markdown", ""))
        if len(answer_markdown) > 100_000:
            raise HTTPException(413, "Câu trả lời vượt 100.000 ký tự.")
        artifact_ids = item.get("artifact_ids")
        if not isinstance(artifact_ids, list):
            artifact_ids = []
        cleaned_artifacts = []
        for artifact_id in artifact_ids:
            artifact_id = str(artifact_id)
            if artifact_id in allowed_artifacts and artifact_id not in cleaned_artifacts:
                cleaned_artifacts.append(artifact_id)
            else:
                raise HTTPException(403, "Biểu đồ không thuộc bài làm của bạn hoặc không tồn tại.")
        existing = db.scalar(select(SubmissionAnswer).where(SubmissionAnswer.submission_id == submission.id, SubmissionAnswer.question_id == question.id))
        if existing:
            existing.answer_markdown = answer_markdown
            existing.selected_artifacts_json = json.dumps(cleaned_artifacts, ensure_ascii=False)
        else:
            db.add(SubmissionAnswer(submission_id=submission.id, question_id=question.id,
                                    answer_markdown=answer_markdown, selected_artifacts_json=json.dumps(cleaned_artifacts, ensure_ascii=False)))
    # Keep a combined draft for compatibility with the shared gallery.
    db.flush()
    combined = build_combined_markdown(db, submission, questions)
    submission.draft_markdown = combined
    db.commit()
    answers = db.scalars(select(SubmissionAnswer).where(SubmissionAnswer.submission_id == submission.id)).all()
    return {"answers": answer_views(db, answers)}


def build_combined_markdown(db: Session, submission: Submission, questions: list[AssignmentQuestion]) -> str:
    answers = db.scalars(select(SubmissionAnswer).where(SubmissionAnswer.submission_id == submission.id)).all()
    by_question = {a.question_id: a for a in answers}
    parts = []
    for question in questions:
        answer = by_question.get(question.id)
        text = (answer.answer_markdown.strip() if answer else "")
        if text:
            for artifact_id in json_load(answer.selected_artifacts_json, []):
                artifact = db.get(Artifact, artifact_id)
                link = f"/api/assets/{artifact_id}"
                if artifact and link not in text:
                    label = "![Biểu đồ]" if artifact.media_type.startswith("image/") else "[Tải bằng chứng]"
                    text += f"\n\n{label}({link})"
            parts.append(f"## Câu hỏi {question.question_order}\n\n{question.question_text}\n\n{text}")
    return "\n\n".join(parts)


def enqueue_job(db: Session, assignment: Assignment, user: User, kind: str, prompt: str,
                submission_id: int | None = None, version_id: int | None = None, question_id: int | None = None) -> AIJob:
    """Create a queued AI job for the async worker to claim."""
    job = AIJob(owner_id=user.id, assignment_id=assignment.id, submission_id=submission_id,
                version_id=version_id, question_id=question_id, kind=kind, prompt=prompt)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def require_exam_draft(db: Session, assignment: Assignment, user: User):
    classroom = can_access_assignment(db, assignment, user)
    if classroom.owner_id != user.id:
        raise HTTPException(403, "Chỉ giáo viên của lớp có thể tạo đề bằng AI.")
    if assignment.status != "draft":
        raise HTTPException(409, "Chỉ tạo và áp dụng đề AI khi bài tập còn là bản nháp.")


@app.post("/api/assignments/{assignment_id}/ai/generate-exam")
def generate_exam_draft(assignment_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    require_exam_draft(db, assignment, user)
    if not dataset_items(assignment):
        raise HTTPException(422, "Tải dataset trước khi tạo câu hỏi và đáp án bằng AI.")
    count = payload.get("count", 3)
    difficulty = payload.get("difficulty", "medium")
    instructions = payload.get("instructions", "")
    if type(count) is not int or not 1 <= count <= 20 or not isinstance(difficulty, str) or difficulty not in {"easy", "medium", "hard"} or not isinstance(instructions, str) or len(instructions) > 4000:
        raise HTTPException(422, "Chọn 1–20 câu, độ khó hợp lệ và yêu cầu tối đa 4.000 ký tự.")
    active = db.scalar(select(AIJob).where(AIJob.assignment_id == assignment.id, AIJob.kind == "exam_generation", AIJob.status.in_(["queued", "running"])))
    if active:
        return {"job_id": active.id, "status": active.status}
    prompt = json.dumps({"count": count, "difficulty": difficulty, "instructions": instructions,
                         "title": assignment.title, "description": assignment.description, "dataset_signature": assignment.dataset_json}, ensure_ascii=False)
    job = enqueue_job(db, assignment, user, "exam_generation", prompt)
    return {"job_id": job.id, "status": job.status}


@app.post("/api/assignments/{assignment_id}/ai/apply-exam")
def apply_exam_draft(assignment_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    require_exam_draft(db, assignment, user)
    job_id = payload.get("job_id")
    job = db.get(AIJob, job_id) if type(job_id) is int else None
    if not job or job.assignment_id != assignment.id or job.kind != "exam_generation" or job.owner_id != user.id:
        raise HTTPException(404, "Không tìm thấy đề AI của bài tập này.")
    if job.status != "done":
        raise HTTPException(409, "Đợi AI tạo xong đề trước khi áp dụng.")
    if json_load(job.prompt, {}).get("dataset_signature") != assignment.dataset_json:
        raise HTTPException(409, "Dataset đã thay đổi. Hãy tạo lại đề AI trên dataset hiện tại.")
    cleaned = normalize_questions(payload)
    raw_by_order = {int(item["question_order"]): item for item in payload["questions"]}
    for item in cleaned:
        answer = raw_by_order[item["question_order"]].get("answer_markdown")
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 20000:
            raise HTTPException(422, "Mỗi câu cần đáp án mẫu từ 1 đến 20.000 ký tự.")
    note = payload.get("note", "")
    if not isinstance(note, str) or len(note) > 8000:
        raise HTTPException(422, "Ghi chú không hợp lệ.")
    questions = sync_questions(db, assignment, {"questions": cleaned})
    generated_artifacts = db.scalars(select(Artifact).where(Artifact.job_id == job.id)).all()
    answers = [{"question_id": q.id, "question_order": q.question_order,
                "answer_markdown": raw_by_order[q.question_order]["answer_markdown"].strip(),
                "artifact_ids": [art.id for art in generated_artifacts if f"/api/assets/{art.id}" in raw_by_order[q.question_order]["answer_markdown"]]} for q in questions]
    assignment.answer_key = "\n\n".join(f"Câu hỏi {q.question_order}: {q.question_text}\n\n{a['answer_markdown']}" for q, a in zip(questions, answers))
    selected_ids = {artifact_id for a in answers for artifact_id in a["artifact_ids"]}
    assignment.reference_answer_json = json.dumps({"answers": answers, "note": note,
        "artifacts": [{"id": art.id, "name": art.display_name, "media_type": art.media_type, "url": f"/api/assets/{art.id}"} for art in generated_artifacts if art.id in selected_ids]}, ensure_ascii=False)
    assignment.reference_published = False
    result = json_load(job.result_json, {})
    result["questions"] = [{**q, "answer_markdown": raw_by_order[q["question_order"]]["answer_markdown"].strip()} for q in cleaned]
    result["note"] = note
    result["applied_at"] = utcnow().isoformat()
    job.result_json = json.dumps(result, ensure_ascii=False)
    db.commit()
    return assignment_view(db, assignment, user)


@app.post("/api/assignments/{assignment_id}/ai/chat")
def ai_chat(assignment_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    rate_limit(f"ai:{user.id}", 18)
    assignment = current_assignment(db, assignment_id)
    require_work_access(db, assignment, user)
    question_text = str(payload.get("question", "")).strip()
    if not question_text or len(question_text) > 8000:
        raise HTTPException(422, "Câu hỏi cần từ 1 đến 8.000 ký tự.")
    question_id = None
    if payload.get("question_id") is not None:
        try:
            question_id = int(payload["question_id"])
        except (TypeError, ValueError):
            raise HTTPException(422, "Câu hỏi bài tập không hợp lệ.")
        if not db.get(AssignmentQuestion, question_id) or db.get(AssignmentQuestion, question_id).assignment_id != assignment.id:
            raise HTTPException(422, "Câu hỏi không thuộc bài tập này.")
    target = db.get(AssignmentQuestion, question_id) if question_id else None
    prompt = json.dumps({"title": assignment.title, "question_id": question_id,
                         "question_text": target.question_text if target else assignment.description,
                         "request": question_text}, ensure_ascii=False)
    job = enqueue_job(db, assignment, user, "chat", prompt, question_id=question_id)
    return {"job_id": job.id, "status": job.status}


@app.post("/api/assignments/{assignment_id}/questions/{question_id}/hints")
def request_question_hints(assignment_id: int, question_id: int, db: Session = Depends(get_db),
                           user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    if assignment.status != "published" or user.role != "student":
        raise HTTPException(403, "Gợi ý dành cho sinh viên làm bài đã công bố.")
    question = db.get(AssignmentQuestion, question_id)
    if not question or question.assignment_id != assignment.id:
        raise HTTPException(404, "Không tìm thấy câu hỏi của bài tập.")
    prompt = json.dumps({"title": assignment.title, "question_id": question.id,
                         "question_text": question.question_text}, ensure_ascii=False)
    existing = db.scalar(select(AIJob).where(AIJob.assignment_id == assignment.id,
        AIJob.owner_id == user.id, AIJob.kind == "question_hint", AIJob.prompt == prompt,
        AIJob.status.in_(["queued", "running", "done"])).order_by(AIJob.id.desc()))
    if existing:
        return {"job_id": existing.id, "status": existing.status}
    rate_limit(f"hints:{user.id}", 18)
    job = enqueue_job(db, assignment, user, "question_hint", prompt, question_id=question.id)
    return {"job_id": job.id, "status": job.status}


@app.post("/api/assignments/{assignment_id}/ai/review")
def review_draft(assignment_id: int, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    rate_limit(f"ai:{user.id}", 18)
    assignment = current_assignment(db, assignment_id)
    require_work_access(db, assignment, user)
    submission = get_or_create_submission(db, assignment.id, user.id)
    questions = ordered_questions(db, assignment)
    answers = db.scalars(select(SubmissionAnswer).where(SubmissionAnswer.submission_id == submission.id)).all()
    by_question = {a.question_id: a for a in answers}
    answered = [q for q in questions if by_question.get(q.id) and by_question.get(q.id).answer_markdown.strip()]
    if not answered:
        raise HTTPException(422, "Hãy viết câu trả lời trước khi xin góp ý.")
    job = enqueue_job(db, assignment, user, "draft_review", json.dumps(_review_payload(db, assignment, questions, answers), ensure_ascii=False), submission.id)
    return {"job_id": job.id, "status": job.status}


def _review_payload(db: Session, assignment: Assignment, questions: list[AssignmentQuestion], answers: list[SubmissionAnswer]) -> dict:
    by_question = {a.question_id: a for a in answers}
    question_entries = []
    for question in questions:
        answer = by_question.get(question.id)
        question_entries.append({
            "question_id": question.id,
            "question_order": question.question_order,
            "question_text": question.question_text,
            "answer_markdown": (answer.answer_markdown if answer else ""),
            "artifacts": json_load(answer.selected_artifacts_json, []) if answer else [],
        })
    return {"questions": question_entries, "assignment_title": assignment.title, "assignment_description": assignment.description}


@app.post("/api/assignments/{assignment_id}/submit")
def submit_assignment(assignment_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    require_work_access(db, assignment, user)
    submission = get_or_create_submission(db, assignment.id, user.id)
    questions = ordered_questions(db, assignment)
    answers = ensure_submission_answers(db, submission, assignment, questions)
    question_by_id = {q.id: q for q in questions}
    snapshot = [{**answer, "question_order": question_by_id[answer["question_id"]].question_order,
                 "question_text": question_by_id[answer["question_id"]].question_text} for answer in answer_views(db, answers)]
    combined = build_combined_markdown(db, submission, questions)
    submission.draft_markdown = combined
    latest = db.scalar(select(SubmissionVersion).where(SubmissionVersion.submission_id == submission.id).order_by(SubmissionVersion.version_number.desc()))
    reflection = str(payload.get("reflection", "")).strip()
    if len(reflection) > 4000:
        raise HTTPException(422, "Ghi chú cải thiện không vượt quá 4.000 ký tự.")
    version = SubmissionVersion(submission_id=submission.id, version_number=(latest.version_number + 1 if latest else 1),
                               body_markdown=combined, answers_snapshot_json=json.dumps(snapshot, ensure_ascii=False),
                               is_improvement=utc(assignment.due_at) <= utcnow(), reflection=reflection)
    db.add(version)
    db.flush()
    submission.grade_json = None
    submission.grade_published = False
    submission.teacher_comment = None
    prompt = json.dumps(_review_payload(db, assignment, questions, answers), ensure_ascii=False)
    job = AIJob(owner_id=user.id, assignment_id=assignment.id, submission_id=submission.id, version_id=version.id, kind="submitted_review", prompt=prompt)
    db.add(job)
    db.commit()
    return {"submission_id": submission.id, "version_id": version.id, "version_number": version.version_number,
            "is_improvement": version.is_improvement, "job_id": job.id}


@app.post("/api/submissions/{submission_id}/ai/review")
def retry_submitted_review(submission_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    rate_limit(f"ai:{user.id}", 18)
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(404, "Không tìm thấy bài nộp.")
    assignment = current_assignment(db, submission.assignment_id)
    classroom = can_access_assignment(db, assignment, user)
    if submission.student_id != user.id and classroom.owner_id != user.id:
        raise HTTPException(403, "Bạn không có quyền đánh giá AI bài này.")
    version = db.get(SubmissionVersion, payload_version_id(payload))
    if not version or version.submission_id != submission.id:
        raise HTTPException(422, "Phiên bản không thuộc bài nộp này.")
    active = db.scalar(select(AIJob).where(AIJob.version_id == version.id, AIJob.kind == "submitted_review", AIJob.status.in_(["queued", "running"])))
    if active:
        return {"job_id": active.id, "status": active.status}
    questions = {q.id: q for q in ordered_questions(db, assignment)}
    entries = [{"question_id": a["question_id"], "question_order": a.get("question_order", questions[a["question_id"]].question_order),
                "question_text": a.get("question_text", questions[a["question_id"]].question_text), "answer_markdown": a["answer_markdown"],
                "artifacts": [x["id"] for x in a.get("artifacts", [])]} for a in json_load(version.answers_snapshot_json, []) if a["question_id"] in questions]
    prompt = json.dumps({"questions": entries, "assignment_title": assignment.title, "assignment_description": assignment.description}, ensure_ascii=False) if entries else version.body_markdown
    job = enqueue_job(db, assignment, db.get(User, submission.student_id), "submitted_review", prompt, submission.id, version.id)
    return {"job_id": job.id, "status": job.status}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    job = db.get(AIJob, job_id)
    if not job:
        raise HTTPException(404, "Không tìm thấy tác vụ.")
    assignment = current_assignment(db, job.assignment_id)
    classroom = db.get(Classroom, assignment.classroom_id)
    if job.owner_id != user.id and classroom.owner_id != user.id:
        raise HTTPException(403, "Không có quyền xem tác vụ.")
    if job.kind in {"chat", "question_hint"}:
        can_access_assignment(db, assignment, user)
    if job.kind == "peer_comparison":
        can_access_assignment(db, assignment, user)
        validate_saved_comparison(db, assignment, db.get(User, job.owner_id), json_load(job.prompt, {}))
    result = {"id": job.id, "kind": job.kind, "status": job.status, "result": json_load(job.result_json, None), "error": job.error_message}
    if job.kind == "exam_generation":
        context = json_load(job.prompt, {})
        result["settings"] = {key: context.get(key) for key in ["count", "difficulty", "instructions"]}
    return result


@app.get("/api/assignments/{assignment_id}/ai/comparisons")
def comparison_history(assignment_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    sources = comparison_sources(db, assignment, user)
    jobs = db.scalars(select(AIJob).where(AIJob.assignment_id == assignment.id, AIJob.owner_id == user.id,
                                         AIJob.kind == "peer_comparison").order_by(AIJob.id.desc()).limit(50)).all()
    history = []
    for job in jobs:
        context = json_load(job.prompt, {})
        try:
            validate_saved_comparison(db, assignment, user, context)
        except HTTPException:
            continue
        history.append({"id": job.id, "status": job.status, "created_at": utc(job.created_at).isoformat(),
                        "mode": context.get("mode", "peers"),
                        "base_version_id": context["base"]["version_id"],
                        "peer_version_ids": [p["version_id"] for p in context["peers"]],
                        "result": json_load(job.result_json, None), "error": job.error_message})
    return {"sources": sources, "history": history}


@app.post("/api/assignments/{assignment_id}/ai/compare-submissions")
def request_comparison(assignment_id: int, payload: dict, db: Session = Depends(get_db),
                       user: User = Depends(require_user), _: None = Depends(require_csrf)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    context = build_comparison_context(db, assignment, user, payload.get("base_version_id"), payload.get("peer_version_ids"), payload.get("mode", "peers"))
    prompt = json.dumps(context, ensure_ascii=False)
    existing = db.scalar(select(AIJob).where(AIJob.assignment_id == assignment.id, AIJob.owner_id == user.id,
                                            AIJob.kind == "peer_comparison", AIJob.prompt == prompt,
                                            AIJob.status.in_(["queued", "running", "done"])).order_by(AIJob.id.desc()))
    if existing:
        return {"job_id": existing.id, "status": existing.status}
    rate_limit(f"comparison:{user.id}", 5, 60)
    job = enqueue_job(db, assignment, user, "peer_comparison", prompt, version_id=context["base"]["version_id"])
    return {"job_id": job.id, "status": job.status}


@app.get("/api/assignments/{assignment_id}/ai/history")
def ai_history(assignment_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    assignment = current_assignment(db, assignment_id)
    can_access_assignment(db, assignment, user)
    jobs = db.scalars(select(AIJob).where(AIJob.owner_id == user.id, AIJob.assignment_id == assignment.id, AIJob.kind == "chat", AIJob.status == "done").order_by(AIJob.created_at)).all()
    result = []
    for job in jobs:
        question_order = None
        if job.question_id:
            question = db.get(AssignmentQuestion, job.question_id)
            question_order = question.question_order if question else None
        context = json_load(job.prompt, {}) if job.prompt.startswith("{") else {}
        result.append({"question": context.get("request", job.prompt.split("Yêu cầu hiện tại:\n")[-1]), "answer": json_load(job.result_json, {}).get("answer", ""),
                       "question_id": job.question_id, "question_order": question_order, "created_at": utc(job.created_at).isoformat()})
    return result


@app.get("/api/assignments/{assignment_id}/submissions")
def list_submissions(assignment_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    assignment = current_assignment(db, assignment_id)
    classroom = can_access_assignment(db, assignment, user)
    if classroom.owner_id != user.id:
        submission = db.scalar(select(Submission).where(Submission.assignment_id == assignment.id, Submission.student_id == user.id))
        if not submission:
            return []
        versions = db.scalars(select(SubmissionVersion).where(SubmissionVersion.submission_id == submission.id).order_by(SubmissionVersion.version_number.desc())).all()
        answers = db.scalars(select(SubmissionAnswer).where(SubmissionAnswer.submission_id == submission.id)).all()
        return [{"student": user.full_name, **submission_view(submission, versions, answers=answer_views(db, answers), db=db)}]
    submissions = db.scalars(select(Submission).where(Submission.assignment_id == assignment.id)).all()
    result = []
    for submission in submissions:
        student = db.get(User, submission.student_id)
        versions = db.scalars(select(SubmissionVersion).where(SubmissionVersion.submission_id == submission.id).order_by(SubmissionVersion.version_number.desc())).all()
        answers = db.scalars(select(SubmissionAnswer).where(SubmissionAnswer.submission_id == submission.id)).all()
        result.append({"student": student.full_name, "email": student.email, "student_id": student.id,
                       **submission_view(submission, versions, include_private=False, answers=answer_views(db, answers), db=db)})
    return result


@app.post("/api/submissions/{submission_id}/grade")
def grade_submission(submission_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    teacher_only(user)
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(404, "Không tìm thấy bài nộp.")
    assignment = current_assignment(db, submission.assignment_id)
    classroom = can_access_assignment(db, assignment, user)
    if classroom.owner_id != user.id:
        raise HTTPException(403, "Chỉ giáo viên của lớp có thể chấm.")
    latest = latest_version(db, submission)
    version = db.get(SubmissionVersion, payload_version_id(payload)) if "version_id" in payload else latest
    if not latest:
        raise HTTPException(409, "Sinh viên chưa có phiên bản bài nộp.")
    if not version or version.submission_id != submission.id:
        raise HTTPException(422, "Phiên bản không thuộc bài nộp này.")
    questions = ordered_questions(db, assignment)
    scores = payload.get("scores", {})
    if not isinstance(scores, dict):
        raise HTTPException(422, "Dữ liệu điểm không hợp lệ.")
    feedback = payload.get("feedback", {})
    if not isinstance(feedback, dict):
        feedback = {}
    comment = str(payload.get("comment", ""))[:4000]
    publish = bool(payload.get("publish", True))

    # Question-based grading: scores are keyed by question id.
    question_keys = {str(q.id) for q in questions}
    scores_keyed_by_question = bool(question_keys) and all(str(k) in question_keys for k in scores)
    if scores_keyed_by_question:
        total = 0.0
        max_score = 0.0
        per_question = []
        for question in questions:
            key = str(question.id)
            try:
                score = float(scores.get(key, 0))
            except (ValueError, TypeError):
                raise HTTPException(422, f"Điểm Câu hỏi {question.question_order} không hợp lệ.")
            if not math.isfinite(score) or score < 0 or score > float(question.max_score):
                raise HTTPException(422, f"Điểm Câu hỏi {question.question_order} vượt giới hạn ({question.max_score:g}).")
            total += score
            max_score += float(question.max_score)
            per_question.append({"question_id": question.id, "question_order": question.question_order,
                                 "score": score, "max_score": float(question.max_score),
                                 "feedback": str(feedback.get(key, ""))[:4000]})
        version.grade_json = json.dumps({"total": round(total, 2), "max_score": round(max_score, 2),
                                            "per_question": per_question}, ensure_ascii=False)
    else:
        # Legacy rubric-based grading (kept for backwards compatibility).
        criteria = json_load(assignment.rubric_json, [])
        total = 0.0
        normalized = []
        for criterion in criteria:
            key = criterion["id"]
            try:
                score = float(scores.get(key, 0))
            except (ValueError, TypeError):
                raise HTTPException(422, "Điểm tiêu chí không hợp lệ.")
            if not math.isfinite(score) or score < 0 or score > float(criterion["max_points"]):
                raise HTTPException(422, f"Điểm tiêu chí {criterion['title']} vượt giới hạn.")
            total += score
            normalized.append({"criterion_id": key, "title": criterion["title"], "score": score, "max_points": criterion["max_points"]})
        version.grade_json = json.dumps({"total": round(total, 2), "max_score": 10, "criteria": normalized}, ensure_ascii=False)
    version.teacher_comment = comment
    version.grade_published = publish
    if version.id == latest.id:
        submission.grade_json = version.grade_json
        submission.teacher_comment = comment
        submission.grade_published = publish
    db.commit()
    return {"grade": json_load(version.grade_json, None), "published": version.grade_published, "version_id": version.id}


@app.post("/api/submissions/{submission_id}/share")
def toggle_share(submission_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    submission = db.get(Submission, submission_id)
    if not submission or submission.student_id != user.id:
        raise HTTPException(404, "Không tìm thấy bài nộp.")
    assignment = current_assignment(db, submission.assignment_id)
    can_access_assignment(db, assignment, user)
    if assignment.share_mode != "opt_in":
        raise HTTPException(409, "Giáo viên đã đặt chia sẻ tất cả bài nộp theo lịch của lớp.")
    if not sharing_open(assignment) or not latest_version(db, submission):
        raise HTTPException(409, "Chỉ có thể chia sẻ bài đã nộp khi đến giờ mở chia sẻ.")
    submission.shared = bool(payload.get("shared", False))
    db.commit()
    return {"shared": submission.shared}


@app.get("/api/classes/{class_id}/gallery")
def gallery(class_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    can_access_class(db, class_id, user)
    assignments = db.scalars(select(Assignment).where(Assignment.classroom_id == class_id, Assignment.status == "published")).all()
    result = []
    for assignment in assignments:
        if not sharing_open(assignment):
            continue
        query = select(Submission).where(Submission.assignment_id == assignment.id)
        if assignment.share_mode == "opt_in":
            query = query.where(Submission.shared.is_(True))
        submissions = db.scalars(query).all()
        own = db.scalar(select(Submission).where(Submission.assignment_id == assignment.id, Submission.student_id == user.id))
        own_version = latest_version(db, own) if own else None
        for submission in submissions:
            versions = db.scalars(select(SubmissionVersion).where(SubmissionVersion.submission_id == submission.id).order_by(SubmissionVersion.version_number.desc())).all()
            if not versions:
                continue
            version = versions[0]
            result.append({"submission_id": submission.id, "assignment_id": assignment.id, "assignment_title": assignment.title,
                           "student_id": submission.student_id, "is_mine": submission.student_id == user.id,
                           "student": db.get(User, submission.student_id).full_name, "body_markdown": version_markdown(version),
                           "version_number": version.version_number, "version_id": version.id,
                           "my_body_markdown": version_markdown(own_version) if own_version else None,
                           "my_version_number": own_version.version_number if own_version else None,
                           "can_review": user.role == "student" and submission.student_id != user.id,
                           "versions": [{"id": v.id, "version_number": v.version_number, "body_markdown": version_markdown(v),
                                         "submitted_at": utc(v.submitted_at).isoformat(), "is_improvement": v.is_improvement, "reflection": v.reflection,
                                         "peer_reviews": [peer_review_view(db, p, user) for p in db.scalars(select(PeerReview).where(PeerReview.version_id == v.id).order_by(PeerReview.created_at)).all()]}
                                        for v in versions], "comments": [],
                           "vote_count": len(db.scalars(select(SubmissionVote.id).where(SubmissionVote.submission_id == submission.id)).all()),
                           "has_voted": bool(db.scalar(select(SubmissionVote.id).where(SubmissionVote.submission_id == submission.id, SubmissionVote.voter_id == user.id)))})
    for item in result:
        comments = db.scalars(select(Comment).where(Comment.submission_id == item["submission_id"]).order_by(Comment.created_at)).all()
        item["comments"] = [{"id": c.id, "author": db.get(User, c.author_id).full_name, "author_id": c.author_id, "body": c.body, "created_at": utc(c.created_at).isoformat()} for c in comments]
    return result


@app.put("/api/submissions/{submission_id}/vote")
def vote_submission(submission_id: int, payload: dict, db: Session = Depends(get_db),
                    user: User = Depends(require_user), _: None = Depends(require_csrf)):
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(404, "Không tìm thấy bài nộp.")
    visible_submission(db, submission, user)
    if submission.student_id == user.id:
        raise HTTPException(403, "Bạn không thể bình chọn bài của mình.")
    if type(payload.get("voted")) is not bool:
        raise HTTPException(422, "Trạng thái bình chọn phải là true hoặc false.")
    # Serialize concurrent vote updates on SQLite, including repeated requests.
    from sqlalchemy import update
    db.execute(update(Submission).where(Submission.id == submission.id).values(updated_at=Submission.updated_at))
    vote = db.scalar(select(SubmissionVote).where(SubmissionVote.submission_id == submission.id, SubmissionVote.voter_id == user.id))
    if payload["voted"] and not vote:
        db.add(SubmissionVote(submission_id=submission.id, voter_id=user.id))
    elif not payload["voted"] and vote:
        db.delete(vote)
    db.commit()
    return {"voted": payload["voted"], "vote_count": len(db.scalars(select(SubmissionVote.id).where(SubmissionVote.submission_id == submission.id)).all())}


@app.put("/api/submissions/{submission_id}/peer-reviews")
def save_peer_review(submission_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(404, "Không tìm thấy bài nộp.")
    visible_submission(db, submission, user)
    if user.role != "student" or submission.student_id == user.id:
        raise HTTPException(403, "Đánh giá chéo dành cho sinh viên nhận xét bài của bạn khác.")
    version = db.get(SubmissionVersion, payload_version_id(payload))
    if not version or version.submission_id != submission.id:
        raise HTTPException(422, "Phiên bản không thuộc bài nộp này.")
    rating = payload.get("rating")
    if type(rating) is not int or not 1 <= rating <= 5:
        raise HTTPException(422, "Mức đánh giá phải là số nguyên từ 1 đến 5.")
    if any(not isinstance(payload.get(key), str) for key in ("strengths", "suggestions", "learned")):
        raise HTTPException(422, "Các phần đánh giá chéo phải là nội dung văn bản.")
    fields = {key: payload[key].strip() for key in ("strengths", "suggestions", "learned")}
    if any(not value or len(value) > 2000 for value in fields.values()):
        raise HTTPException(422, "Hãy ghi điểm tốt, góp ý và điều bạn học được; mỗi phần từ 1 đến 2.000 ký tự.")
    review = db.scalar(select(PeerReview).where(PeerReview.version_id == version.id, PeerReview.reviewer_id == user.id))
    if not review:
        review = PeerReview(version_id=version.id, reviewer_id=user.id, rating=rating, **fields)
        db.add(review)
    else:
        review.rating = rating
        for key, value in fields.items():
            setattr(review, key, value)
    db.commit()
    return peer_review_view(db, review, user)


@app.post("/api/submissions/{submission_id}/comments")
def add_comment(submission_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(404, "Không tìm thấy bài nộp.")
    visible_submission(db, submission, user)
    body = str(payload.get("body", "")).strip()
    if not body or len(body) > 2000:
        raise HTTPException(422, "Bình luận cần từ 1 đến 2.000 ký tự.")
    item = Comment(submission_id=submission.id, author_id=user.id, body=body)
    db.add(item)
    db.commit()
    return {"id": item.id, "body": item.body, "author": user.full_name, "author_id": user.id, "created_at": utc(item.created_at).isoformat()}


@app.delete("/api/comments/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), user: User = Depends(require_user), _: None = Depends(require_csrf)):
    item = db.get(Comment, comment_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy bình luận.")
    submission = db.get(Submission, item.submission_id)
    assignment = current_assignment(db, submission.assignment_id)
    classroom = can_access_assignment(db, assignment, user)
    if item.author_id != user.id and classroom.owner_id != user.id:
        raise HTTPException(403, "Bạn không thể xóa bình luận này.")
    db.delete(item)
    db.commit()
    return {"ok": True}


@app.get("/api/assets/{artifact_id}")
def get_asset(artifact_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    artifact = db.scalar(select(Artifact).where(Artifact.id == artifact_id))
    if not artifact:
        raise HTTPException(404, "Không tìm thấy biểu đồ hoặc tệp.")
    job = db.get(AIJob, artifact.job_id)
    assignment = current_assignment(db, job.assignment_id)
    classroom = db.get(Classroom, assignment.classroom_id)
    is_owner = job.owner_id == user.id
    is_teacher = classroom.owner_id == user.id
    if not is_owner and not is_teacher:
        reference = json_load(assignment.reference_answer_json, {})
        own_submission = db.scalar(select(Submission).where(Submission.assignment_id == assignment.id, Submission.student_id == user.id))
        can_view_reference_asset = (job.kind == "exam_generation" and assignment.status == "published" and assignment.reference_published
                                    and own_submission and latest_version(db, own_submission)
                                    and any(f"/api/assets/{artifact_id}" in a.get("answer_markdown", "") for a in reference.get("answers", [])))
        shared_submission = db.scalar(select(Submission).where(Submission.assignment_id == assignment.id, Submission.student_id == job.owner_id))
        shared_versions = db.scalars(select(SubmissionVersion).where(SubmissionVersion.submission_id == shared_submission.id)).all() if shared_submission else []
        referenced = any(f"/api/assets/{artifact_id}" in version_markdown(v) for v in shared_versions)
        allowed = shared_submission and sharing_open(assignment) and (assignment.share_mode == "all" or shared_submission.shared)
        if not ((referenced and allowed) or can_view_reference_asset) or not db.scalar(select(Membership.id).where(Membership.classroom_id == classroom.id, Membership.user_id == user.id)):
            raise HTTPException(403, "Bạn không có quyền xem tệp này.")
    path = Path(artifact.local_path).resolve()
    if not path.is_file() or not path.is_relative_to(ARTIFACT_DIR.resolve()):
        raise HTTPException(404, "Tệp không còn khả dụng.")
    inline = artifact.media_type.startswith("image/")
    return FileResponse(path, media_type=artifact.media_type, filename=artifact.display_name, content_disposition_type="inline" if inline else "attachment")

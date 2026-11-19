"""SQLite-backed single-host worker for graph and review tasks."""
import json
import logging
import time
from pathlib import Path
from datetime import timedelta

from sqlalchemy import select, update

from .ai_service import review_answers, review_submission, run_graph, tutor_reply
from .exam_generation import generate_exam
from .peer_comparison import compare_reports, validate_saved_comparison
from .question_hints import question_hints
from .config import UPLOAD_DIR
from .database import SessionLocal
from .models import AIJob, Artifact, Assignment, SubmissionVersion, User, utcnow


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("web02.worker")


def _claim(db) -> AIJob | None:
    candidate_id = db.scalar(select(AIJob.id).where(AIJob.status == "queued").order_by(AIJob.created_at).limit(1))
    if candidate_id is None:
        return None
    claimed = db.execute(update(AIJob).where(AIJob.id == candidate_id, AIJob.status == "queued").values(status="running", updated_at=utcnow())).rowcount
    db.commit()
    if not claimed:
        return None
    return db.get(AIJob, candidate_id)


def _files(assignment: Assignment) -> list[str]:
    result = []
    for item in json.loads(assignment.dataset_json or "[]"):
        path = Path(item["path"]).resolve()
        if not path.is_file() or not path.is_relative_to(UPLOAD_DIR.resolve()):
            raise RuntimeError("Dataset bị thiếu hoặc nằm ngoài thư mục dữ liệu được phép.")
        result.append(str(path))
    if not result:
        raise RuntimeError("Bài tập không có dataset.")
    return result


def _execute(job_id: int):
    db = SessionLocal()
    try:
        job = db.get(AIJob, job_id)
        assignment = db.get(Assignment, job.assignment_id)
        kind, prompt = job.kind, job.prompt
        files = _files(assignment) if kind not in {"peer_comparison", "question_hint", "chat"} else []
        if kind == "peer_comparison":
            validate_saved_comparison(db, assignment, db.get(User, job.owner_id), json.loads(prompt))
        rubric = json.loads(assignment.rubric_json or "[]")
        answer_key = assignment.answer_key
        version_id = job.version_id
    finally:
        db.close()

    if kind == "peer_comparison":
        result = compare_reports(json.loads(prompt))
        artifacts = []
    elif kind == "exam_generation":
        context = json.loads(prompt)
        if context["dataset_signature"] != assignment.dataset_json:
            raise RuntimeError("Dataset changed while generating assessment")
        generated = generate_exam(context, files, job_id)
        artifacts = generated.pop("artifacts")
        result = {**generated, "artifacts": [{"id": item["id"], "name": item["name"], "media_type": item["media_type"]} for item in artifacts]}
    elif kind in {"chat", "question_hint"}:
        # Legacy queued chat prompts are still handled, without running a solver.
        context = json.loads(prompt) if prompt.startswith("{") else {"question_text": prompt}
        result = question_hints(context)
        artifacts = []
    elif kind in {"draft_review", "submitted_review"}:
        try:
            payload = json.loads(prompt) if prompt.strip().startswith("{") else None
        except json.JSONDecodeError:
            payload = None
        if payload and isinstance(payload.get("questions"), list):
            review = review_answers(payload, files, rubric, answer_key, job_id)
        else:
            review = review_submission(prompt, files, rubric, answer_key, job_id)
        result = {"checks": review["checks"], "artifacts": [{"id": item["id"], "name": item["name"], "media_type": item["media_type"]} for item in review["artifacts"]]}
        if "overall" in review:
            result["overall"] = review["overall"]
        artifacts = review["artifacts"]
    else:
        raise RuntimeError(f"Unknown AI task type: {kind}")

    db = SessionLocal()
    try:
        job = db.get(AIJob, job_id)
        for item in artifacts:
            db.merge(Artifact(id=item["id"], job_id=job.id, local_path=item["path"], display_name=item["name"], media_type=item["media_type"]))
        job.result_json = json.dumps(result, ensure_ascii=False)
        job.status = "done"
        job.error_message = None
        if version_id:
            version = db.get(SubmissionVersion, version_id)
            if version and "checks" in result:
                version.review_json = json.dumps({"checks": result["checks"], "overall": result.get("overall")}, ensure_ascii=False)
        db.commit()
    finally:
        db.close()


def run_forever():
    db = SessionLocal()
    try:
        # A process killed during a graph call can safely retry the durable job.
        cutoff = utcnow() - timedelta(minutes=30)
        db.execute(update(AIJob).where(AIJob.status == "running", AIJob.updated_at < cutoff).values(status="queued", updated_at=utcnow()))
        db.commit()
    finally:
        db.close()
    logger.info("AI worker started; DA-Agent-drive integration is ready on demand")
    while True:
        db = SessionLocal()
        try:
            job = _claim(db)
            job_id = job.id if job else None
        except Exception:
            db.rollback()
            logger.exception("Could not claim an AI task")
            job_id = None
        finally:
            db.close()
        if job_id is None:
            time.sleep(1)
            continue
        try:
            logger.info("Processing task %s", job_id)
            _execute(job_id)
        except Exception as exc:
            logger.exception("AI task %s failed", job_id)
            db = SessionLocal()
            try:
                job = db.get(AIJob, job_id)
                if job:
                    job.status = "failed"
                    job.error_message = "AI chưa thể xử lý yêu cầu này. Vui lòng thử lại hoặc báo giáo viên nếu lỗi tiếp diễn."
                    db.commit()
            finally:
                db.close()


if __name__ == "__main__":
    run_forever()

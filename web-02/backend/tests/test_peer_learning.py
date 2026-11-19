import json
from datetime import timedelta

from sqlalchemy import select

from test_questions import (
    _clean_db, _make_teacher_class, _create_assignment, _add_dataset_and_publish,
    _join, _login, _csrf, _save_answers, client,
)
from app.database import SessionLocal
from app.models import Assignment, Submission, SubmissionVersion, PeerReview, AIJob, Artifact, User, utcnow
from app.config import ARTIFACT_DIR


def setup_assignment():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    _join(class_id, "student@test.edu")
    _join(class_id, "other@test.edu")
    return class_id, assignment_id


def submit(assignment_id, email="student@test.edu", text="Bài gốc"):
    _login(email)
    questions = client.get(f"/api/assignments/{assignment_id}").json()["questions"]
    response = client.put(f"/api/assignments/{assignment_id}/answers", json={"answers": [
        {"question_id": q["id"], "answer_markdown": f"{text} {q['question_order']}", "artifact_ids": []}
        for q in questions
    ]}, headers={"x-csrf-token": _csrf()})
    assert response.status_code == 200, response.text
    response = client.post(f"/api/assignments/{assignment_id}/submit", json={}, headers={"x-csrf-token": _csrf()})
    assert response.status_code == 200, response.text
    return response.json()


def set_times(assignment_id, due_in=-1, sharing_in=-1, improvements=True, mode="all"):
    with SessionLocal() as db:
        assignment = db.get(Assignment, assignment_id)
        assignment.due_at = utcnow() + timedelta(days=due_in)
        assignment.sharing_open_at = utcnow() + timedelta(days=sharing_in)
        assignment.allow_improvements = improvements
        assignment.share_mode = mode
        db.commit()


def review_payload(version_id):
    return {"version_id": version_id, "rating": 4, "strengths": "Biểu đồ có nhãn rõ.",
            "suggestions": "Bổ sung giới hạn của dữ liệu.", "learned": "Tôi học được cách nhóm theo vùng."}


def test_sharing_time_is_independent_of_due_date_and_enforced():
    class_id, assignment_id = setup_assignment()
    original = submit(assignment_id)
    _login("other@test.edu")
    set_times(assignment_id, due_in=-2, sharing_in=1)
    assert client.get(f"/api/classes/{class_id}/gallery").json() == []
    assert client.put(f"/api/submissions/{original['submission_id']}/peer-reviews", json=review_payload(original["version_id"]), headers={"x-csrf-token": _csrf()}).status_code == 404
    set_times(assignment_id, due_in=1, sharing_in=-1)
    gallery = client.get(f"/api/classes/{class_id}/gallery").json()
    assert len(gallery) == 1
    assert gallery[0]["version_id"] == original["version_id"]
    assert "draft_markdown" not in gallery[0] and "answer_key" not in gallery[0]


def test_peer_review_is_per_version_and_can_update_only_own_review():
    class_id, assignment_id = setup_assignment()
    original = submit(assignment_id)
    set_times(assignment_id)
    _login("student@test.edu")
    assert client.put(f"/api/submissions/{original['submission_id']}/peer-reviews", json=review_payload(original["version_id"]), headers={"x-csrf-token": _csrf()}).status_code == 403
    _login("other@test.edu")
    payload = review_payload(original["version_id"])
    first = client.put(f"/api/submissions/{original['submission_id']}/peer-reviews", json=payload, headers={"x-csrf-token": _csrf()})
    assert first.status_code == 200, first.text
    payload["rating"] = 5
    second = client.put(f"/api/submissions/{original['submission_id']}/peer-reviews", json=payload, headers={"x-csrf-token": _csrf()})
    assert second.json()["id"] == first.json()["id"]
    improved = submit(assignment_id, text="Bài cải thiện")
    _login("other@test.edu")
    entry = client.get(f"/api/classes/{class_id}/gallery").json()[0]
    assert entry["version_id"] == improved["version_id"]
    assert entry["versions"][0]["peer_reviews"] == []
    assert entry["versions"][1]["peer_reviews"][0]["rating"] == 5
    assert "Bài gốc" in entry["versions"][1]["body_markdown"]


def test_improvement_requires_original_submission_and_permission():
    _, assignment_id = setup_assignment()
    original = submit(assignment_id)
    set_times(assignment_id, improvements=False)
    _login("student@test.edu")
    assert client.get(f"/api/assignments/{assignment_id}").json()["can_edit"] is False
    assert client.post(f"/api/assignments/{assignment_id}/submit", json={}, headers={"x-csrf-token": _csrf()}).status_code == 409
    set_times(assignment_id, improvements=True, sharing_in=1)
    assert client.post(f"/api/assignments/{assignment_id}/submit", json={}, headers={"x-csrf-token": _csrf()}).status_code == 409
    set_times(assignment_id)
    improved = submit(assignment_id, text="Cách phân tích mới")
    assert improved["is_improvement"] is True and improved["version_number"] == 2
    _login("other@test.edu")
    assert client.post(f"/api/assignments/{assignment_id}/submit", json={}, headers={"x-csrf-token": _csrf()}).status_code == 409
    with SessionLocal() as db:
        assert "Bài gốc" in db.get(SubmissionVersion, original["version_id"]).body_markdown


def test_hidden_drafts_and_unselected_artifacts_never_become_public():
    class_id, assignment_id = setup_assignment()
    original = submit(assignment_id)
    with SessionLocal() as db:
        owner = db.scalar(select(User).where(User.email == "student@test.edu"))
        job = AIJob(owner_id=owner.id, assignment_id=assignment_id, kind="chat", status="done")
        db.add(job)
        db.flush()
        for name in ("selected", "private"):
            path = ARTIFACT_DIR / f"{name}.png"
            path.write_bytes(b"image")
            db.add(Artifact(id=name, job_id=job.id, local_path=str(path), display_name=name + ".png", media_type="image/png"))
        version = db.get(SubmissionVersion, original["version_id"])
        snapshot = json.loads(version.answers_snapshot_json)
        snapshot[0]["artifacts"] = [{"id": "selected", "media_type": "image/png"}]
        version.answers_snapshot_json = json.dumps(snapshot)
        db.get(Submission, original["submission_id"]).draft_markdown = "SECRET UNSUBMITTED DRAFT"
        db.commit()
    _login("other@test.edu")
    assert client.get("/api/assets/selected").status_code == 403
    set_times(assignment_id)
    gallery = client.get(f"/api/classes/{class_id}/gallery").json()
    assert "SECRET UNSUBMITTED DRAFT" not in json.dumps(gallery)
    assert "/api/assets/selected" in gallery[0]["body_markdown"]
    assert client.get("/api/assets/selected").status_code == 200
    assert client.get("/api/assets/private").status_code == 403
    with SessionLocal() as db:
        owner = db.scalar(select(User).where(User.email == "other@test.edu"))
        from app.models import Membership
        member = db.scalar(select(Membership).where(Membership.user_id == owner.id, Membership.classroom_id == class_id))
        db.delete(member)
        db.commit()
    assert client.get(f"/api/classes/{class_id}/gallery").status_code == 403
    assert client.get("/api/assets/selected").status_code == 403


def test_teacher_grades_saved_version_and_grade_survives_improvement():
    _, assignment_id = setup_assignment()
    original = submit(assignment_id)
    _login("teacher@test.edu")
    questions = client.get(f"/api/assignments/{assignment_id}").json()["questions"]
    payload = {"version_id": original["version_id"], "scores": {str(q["id"]): 7 for q in questions}, "publish": True, "comment": "Bài đầu đạt."}
    response = client.post(f"/api/submissions/{original['submission_id']}/grade", json=payload, headers={"x-csrf-token": _csrf()})
    assert response.status_code == 200, response.text
    set_times(assignment_id)
    submit(assignment_id, text="Bản mới")
    data = client.get(f"/api/assignments/{assignment_id}").json()["submission"]
    assert data["grade"] is None
    assert data["versions"][1]["grade"]["total"] == 21
    assert data["versions"][1]["teacher_comment"] == "Bài đầu đạt."


def test_worker_uses_submission_snapshot_and_retry_deduplicates(monkeypatch):
    _, assignment_id = setup_assignment()
    original = submit(assignment_id)
    questions = client.get(f"/api/assignments/{assignment_id}").json()["questions"]
    _save_answers(assignment_id, [{"question_id": q["id"], "answer_markdown": "UNSUBMITTED NEW DRAFT", "artifact_ids": []} for q in questions])
    from app import worker
    seen = []
    def fake_review(payload, *args):
        seen.append(payload)
        return {"checks": [], "overall": {"quality": "partial", "feedback": "Bổ sung bằng chứng."}, "artifacts": []}
    monkeypatch.setattr(worker, "review_answers", fake_review)
    retry = client.post(f"/api/submissions/{original['submission_id']}/ai/review", json={"version_id": original["version_id"]}, headers={"x-csrf-token": _csrf()})
    assert retry.json()["job_id"] == original["job_id"]
    worker._execute(original["job_id"])
    assert "UNSUBMITTED" not in json.dumps(seen)
    assert "Bài gốc" in json.dumps(seen, ensure_ascii=False)
    version = client.get(f"/api/assignments/{assignment_id}").json()["submission"]["versions"][0]
    assert version["review_status"] == "done" and version["review"]["overall"]["quality"] == "partial"


def test_policy_change_requires_teacher_and_opt_in_is_respected():
    class_id, assignment_id = setup_assignment()
    original = submit(assignment_id)
    set_times(assignment_id, mode="opt_in")
    _login("other@test.edu")
    assert client.get(f"/api/classes/{class_id}/gallery").json() == []
    assert client.put(f"/api/assignments/{assignment_id}/settings", json={"share_mode": "all"}, headers={"x-csrf-token": _csrf()}).status_code == 403
    _login("student@test.edu")
    assert client.post(f"/api/submissions/{original['submission_id']}/share", json={"shared": True}, headers={"x-csrf-token": _csrf()}).status_code == 200
    _login("other@test.edu")
    assert len(client.get(f"/api/classes/{class_id}/gallery").json()) == 1
    _login("teacher@test.edu")
    response = client.put(f"/api/assignments/{assignment_id}/settings", json={"share_mode": "all", "sharing_open_at": "2030-01-02T10:00:00+07:00"}, headers={"x-csrf-token": _csrf()})
    assert response.status_code == 200 and response.json()["sharing_open"] is False
    _login("other@test.edu")
    assert client.get(f"/api/classes/{class_id}/gallery").json() == []


def test_variable_question_count_and_optional_rubric():
    class_id = _make_teacher_class()
    _login("teacher@test.edu")
    response = client.post(f"/api/classes/{class_id}/assignments", json={
        "title": "Một câu hỏi", "due_at": "2030-01-01T00:00:00+07:00", "rubric": [],
        "questions": [{"question_order": 1, "question_text": "Insight chính là gì?", "max_score": 10}],
    }, headers={"x-csrf-token": _csrf()})
    assert response.status_code == 200, response.text
    assignment_id = response.json()["id"]
    _add_dataset_and_publish(assignment_id)
    _join(class_id, "student@test.edu")
    submit(assignment_id)

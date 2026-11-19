"""Backend tests for the 3-question assignment and reference-answer features.

Run with:  .venv/Scripts/python.exe -m pytest tests -q
"""
import os
import sys
from pathlib import Path

# conftest configures a throwaway database before any test module is collected.
_tmp = str(Path(os.environ["WEB02_DATA_DIR"]).parent)

from fastapi.testclient import TestClient  # noqa: E402
import pytest  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app import models  # noqa: F401,E402
from app.main import app  # noqa: E402
import app.main as main_module  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import User, Classroom, Assignment, AssignmentQuestion, Submission, SubmissionVersion, SubmissionAnswer, Artifact, AIJob, utcnow  # noqa: E402
from sqlalchemy import text  # noqa: E402


Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_db():
    """Wipe all rows and rate-limit state between tests."""
    main_module._rate_events.clear()
    with engine.begin() as conn:
        for table in ("submission_votes", "peer_reviews", "comments", "artifacts", "ai_jobs", "submission_answers", "submission_versions",
                      "submissions", "assignment_questions", "assignments", "memberships", "classrooms", "users"):
            conn.execute(text(f"DELETE FROM {table}"))
    yield


def _csrf():
    return client.get("/api/auth/csrf").json()["csrf_token"]


def _register(email: str, name: str, role: str):
    token = _csrf()
    resp = client.post("/api/auth/register", json={"email": email, "full_name": name, "password": "password123", "role": role}, headers={"x-csrf-token": token})
    assert resp.status_code == 200, resp.text
    return resp


def _login(email: str):
    token = _csrf()
    resp = client.post("/api/auth/login", json={"email": email, "password": "password123"}, headers={"x-csrf-token": token})
    assert resp.status_code == 200, resp.text
    return resp


def _teacher_csrf():
    return _csrf()


def _make_teacher_class():
    """Register teacher + student(s), create a class, return ids."""
    _register("teacher@test.edu", "Teacher", "teacher")
    _register("student@test.edu", "Student A", "student")
    _register("other@test.edu", "Other Student", "student")
    _login("teacher@test.edu")
    token = _csrf()
    resp = client.post("/api/classes", json={"name": "Test Class"}, headers={"x-csrf-token": token})
    assert resp.status_code == 200
    return resp.json()["id"]


def _join(class_id: int, email: str):
    # Fetch join code as teacher first, then switch to the student session.
    _login("teacher@test.edu")
    join_code = client.get(f"/api/classes/{class_id}").json()["join_code"]
    _login(email)
    token = _csrf()
    resp = client.post("/api/classes/join", json={"code": join_code}, headers={"x-csrf-token": token})
    assert resp.status_code == 200, resp.text


def _get_join_code(class_id: int):
    _login("teacher@test.edu")
    return client.get(f"/api/classes/{class_id}").json()["join_code"]


def _create_assignment(class_id: int, questions: list[dict] | None = None):
    _login("teacher@test.edu")
    token = _csrf()
    questions = questions if questions is not None else [
        {"question_order": 1, "question_text": "Câu hỏi một là gì?"},
        {"question_order": 2, "question_text": "Câu hỏi hai là gì?"},
        {"question_order": 3, "question_text": "Câu hỏi ba là gì?"},
    ]
    payload = {
        "title": "Bài tập mẫu", "description": "Mô tả chung", "due_at": "2030-01-01T00:00:00+07:00",
        "answer_key": "dap an noi bo",
        "questions": questions,
        "rubric": [
            {"id": "c1", "title": "Tiêu chí 1", "description": "desc", "hint": "hint", "max_points": 5},
            {"id": "c2", "title": "Tiêu chí 2", "description": "desc", "hint": "hint", "max_points": 5},
        ],
    }
    resp = client.post(f"/api/classes/{class_id}/assignments", json=payload, headers={"x-csrf-token": token})
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def _add_dataset_and_publish(assignment_id: int):
    _login("teacher@test.edu")
    token = _csrf()
    import io
    content = "a,b\n1,2\n3,4\n".encode()
    resp = client.post(f"/api/assignments/{assignment_id}/datasets", files=[("files", ("data.csv", content, "text/csv"))], headers={"x-csrf-token": token})
    assert resp.status_code == 200, resp.text
    resp = client.post(f"/api/assignments/{assignment_id}/publish", json={}, headers={"x-csrf-token": token})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _save_answers(assignment_id: int, answers: list[dict]):
    _login("student@test.edu")
    token = _csrf()
    resp = client.put(f"/api/assignments/{assignment_id}/answers", json={"answers": answers}, headers={"x-csrf-token": token})
    assert resp.status_code == 200, resp.text
    return _csrf()  # fresh token for the caller's next write


def test_teacher_cannot_publish_without_any_questions():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _login("teacher@test.edu")
    token = _csrf()
    # remove one question via update endpoint -> now only 2 questions
    resp = client.put(f"/api/assignments/{assignment_id}/questions", json={"questions": [
        {"question_order": 1, "question_text": "Một"},
        {"question_order": 2, "question_text": "Hai"},
    ]}, headers={"x-csrf-token": token})
    assert resp.status_code == 200, resp.text
    # A variable number of questions is allowed; no questions is invalid.
    with SessionLocal() as db:
        from sqlalchemy import delete as sa_delete
        db.execute(sa_delete(AssignmentQuestion).where(AssignmentQuestion.assignment_id == assignment_id))
        db.commit()
    # add dataset so only questions are missing
    import io
    client.post(f"/api/assignments/{assignment_id}/datasets", files=[("files", ("d.csv", "a,b\n1,2\n".encode(), "text/csv"))], headers={"x-csrf-token": token})
    resp = client.post(f"/api/assignments/{assignment_id}/publish", json={}, headers={"x-csrf-token": token})
    assert resp.status_code == 422


def test_teacher_can_add_questions_to_published_legacy_assignment():
    """A published assignment that has no questions (legacy) can still receive its 3 questions."""
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    # Simulate legacy data: assignment was published before questions existed.
    with SessionLocal() as db:
        from sqlalchemy import delete as sa_delete
        db.execute(sa_delete(AssignmentQuestion).where(AssignmentQuestion.assignment_id == assignment_id))
        db.commit()
    _login("teacher@test.edu")
    token = _csrf()
    resp = client.put(f"/api/assignments/{assignment_id}/questions", json={"questions": [
        {"question_order": 1, "question_text": "Một"},
        {"question_order": 2, "question_text": "Hai"},
        {"question_order": 3, "question_text": "Ba"},
    ]}, headers={"x-csrf-token": token})
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["questions"]) == 3
    # Once questions exist on a published assignment, editing is locked.
    token = _csrf()
    resp2 = client.put(f"/api/assignments/{assignment_id}/questions", json={"questions": [
        {"question_order": 1, "question_text": "Đổi"},
        {"question_order": 2, "question_text": "Hai"},
        {"question_order": 3, "question_text": "Ba"},
    ]}, headers={"x-csrf-token": token})
    assert resp2.status_code == 409


def test_student_sees_three_questions_in_order():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    _join(class_id, "student@test.edu")
    _login("student@test.edu")
    data = client.get(f"/api/assignments/{assignment_id}").json()
    orders = [q["question_order"] for q in data["questions"]]
    assert orders == [1, 2, 3]
    assert "answer_key" not in data


def test_student_cannot_submit_missing_answer():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    _join(class_id, "student@test.edu")
    _login("student@test.edu")
    qs = client.get(f"/api/assignments/{assignment_id}").json()["questions"]
    token = _save_answers(assignment_id, [{"question_id": qs[0]["id"], "answer_markdown": "Trả lời 1", "artifact_ids": []}])
    resp = client.post(f"/api/assignments/{assignment_id}/submit", json={}, headers={"x-csrf-token": token})
    assert resp.status_code == 422
    assert "Câu hỏi 2" in resp.json()["detail"]


def test_each_version_keeps_three_answers_snapshot():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    _join(class_id, "student@test.edu")
    _login("student@test.edu")
    qs = client.get(f"/api/assignments/{assignment_id}").json()["questions"]
    token = _csrf()
    answers = [{"question_id": q["id"], "answer_markdown": f"Trả lời {q['question_order']}", "artifact_ids": []} for q in qs]
    token = _save_answers(assignment_id, answers)
    resp1 = client.post(f"/api/assignments/{assignment_id}/submit", json={}, headers={"x-csrf-token": token})
    assert resp1.status_code == 200, resp1.text
    # submit again with changed answer
    answers2 = [{"question_id": q["id"], "answer_markdown": f"Trả lời mới {q['question_order']}", "artifact_ids": []} for q in qs]
    token = _save_answers(assignment_id, answers2)
    resp2 = client.post(f"/api/assignments/{assignment_id}/submit", json={}, headers={"x-csrf-token": token})
    assert resp2.status_code == 200
    _login("teacher@test.edu")
    subs = client.get(f"/api/assignments/{assignment_id}/submissions").json()
    submission = subs[0]
    versions = submission["versions"]
    assert len(versions) >= 2
    snap1 = versions[-1]["answers_snapshot"]
    snap2 = versions[0]["answers_snapshot"]
    assert len(snap1) == 3 and len(snap2) == 3
    assert snap1[0]["answer_markdown"] != snap2[0]["answer_markdown"]


def test_reference_403_when_not_submitted():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    _login("teacher@test.edu")
    token = _csrf()
    qs = client.get(f"/api/assignments/{assignment_id}").json()["questions"]
    client.put(f"/api/assignments/{assignment_id}/reference", json={"answers": [{"question_id": q["id"], "answer_markdown": "Tham khảo"} for q in qs], "note": ""}, headers={"x-csrf-token": token})
    client.post(f"/api/assignments/{assignment_id}/reference/publish", json={"published": True}, headers={"x-csrf-token": token})
    _join(class_id, "student@test.edu")
    _login("student@test.edu")
    resp = client.get(f"/api/assignments/{assignment_id}/reference")
    assert resp.status_code == 403


def test_reference_not_published_hides_content():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    _join(class_id, "student@test.edu")
    _login("student@test.edu")
    qs = client.get(f"/api/assignments/{assignment_id}").json()["questions"]
    answers = [{"question_id": q["id"], "answer_markdown": f"Trả lời {q['question_order']}", "artifact_ids": []} for q in qs]
    token = _save_answers(assignment_id, answers)
    client.post(f"/api/assignments/{assignment_id}/submit", json={}, headers={"x-csrf-token": token})
    resp = client.get(f"/api/assignments/{assignment_id}/reference")
    assert resp.status_code == 404


def test_reference_visible_after_submit_and_publish():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    _join(class_id, "student@test.edu")
    _login("student@test.edu")
    qs = client.get(f"/api/assignments/{assignment_id}").json()["questions"]
    token = _save_answers(assignment_id, [{"question_id": q["id"], "answer_markdown": f"Trả lời {q['question_order']}", "artifact_ids": []} for q in qs])
    client.post(f"/api/assignments/{assignment_id}/submit", json={}, headers={"x-csrf-token": token})
    _login("teacher@test.edu")
    ttoken = _csrf()
    client.put(f"/api/assignments/{assignment_id}/reference", json={"answers": [{"question_id": q["id"], "answer_markdown": f"Tham khảo {q['question_order']}"} for q in qs], "note": "Ghi chú"}, headers={"x-csrf-token": ttoken})
    ttoken = _csrf()
    client.post(f"/api/assignments/{assignment_id}/reference/publish", json={"published": True}, headers={"x-csrf-token": ttoken})
    _login("student@test.edu")
    resp = client.get(f"/api/assignments/{assignment_id}/reference")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["reference"]["answers"]) == 3
    assert data["reference"]["note"] == "Ghi chú"
    assert "answer_key" not in data


def test_other_class_student_cannot_view_reference():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    _join(class_id, "student@test.edu")
    _login("student@test.edu")
    qs = client.get(f"/api/assignments/{assignment_id}").json()["questions"]
    token = _save_answers(assignment_id, [{"question_id": q["id"], "answer_markdown": f"Trả lời {q['question_order']}", "artifact_ids": []} for q in qs])
    client.post(f"/api/assignments/{assignment_id}/submit", json={}, headers={"x-csrf-token": token})
    _login("teacher@test.edu")
    ttoken = _csrf()
    client.put(f"/api/assignments/{assignment_id}/reference", json={"answers": [{"question_id": q["id"], "answer_markdown": "Tham khảo"} for q in qs], "note": ""}, headers={"x-csrf-token": ttoken})
    ttoken = _csrf()
    client.post(f"/api/assignments/{assignment_id}/reference/publish", json={"published": True}, headers={"x-csrf-token": ttoken})
    # other student is in NO class
    _login("other@test.edu")
    resp = client.get(f"/api/assignments/{assignment_id}/reference")
    assert resp.status_code in (403, 404)


def test_student_api_does_not_leak_answer_key():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    _join(class_id, "student@test.edu")
    _login("student@test.edu")
    data = client.get(f"/api/assignments/{assignment_id}").json()
    assert "answer_key" not in data
    assert "reference" not in data  # reference only via dedicated endpoint


def test_cannot_attach_foreign_artifact():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    _join(class_id, "student@test.edu")
    _join(class_id, "other@test.edu")
    _login("student@test.edu")
    qs = client.get(f"/api/assignments/{assignment_id}").json()["questions"]
    token = _csrf()
    resp = client.put(f"/api/assignments/{assignment_id}/answers", json={"answers": [{"question_id": qs[0]["id"], "answer_markdown": "x", "artifact_ids": ["foreign-artifact"]}]}, headers={"x-csrf-token": token})
    assert resp.status_code == 403


def test_teacher_sees_version_history_per_student():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    _add_dataset_and_publish(assignment_id)
    _join(class_id, "student@test.edu")
    _login("student@test.edu")
    qs = client.get(f"/api/assignments/{assignment_id}").json()["questions"]
    for i in range(2):
        token = _save_answers(assignment_id, [{"question_id": q["id"], "answer_markdown": f"Lần {i} câu {q['question_order']}", "artifact_ids": []} for q in qs])
        client.post(f"/api/assignments/{assignment_id}/submit", json={}, headers={"x-csrf-token": token})
    _login("teacher@test.edu")
    subs = client.get(f"/api/assignments/{assignment_id}/submissions").json()
    assert len(subs) == 1
    assert len(subs[0]["versions"]) == 2
    assert all(len(v["answers_snapshot"]) == 3 for v in subs[0]["versions"])


def test_migration_runs_on_legacy_database():
    """Verify all migrations upgrade a 0001 database without data loss."""
    import sqlite3
    import subprocess
    legacy = Path(_tmp) / "legacy.sqlite3"
    conn = sqlite3.connect(str(legacy))
    conn.executescript("""
    CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL);
    INSERT INTO alembic_version VALUES ('0001_initial');
    CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(254) NOT NULL, full_name VARCHAR(120) NOT NULL, password_hash VARCHAR(256) NOT NULL, role VARCHAR(20) NOT NULL, created_at DATETIME NOT NULL);
    CREATE TABLE classrooms (id INTEGER PRIMARY KEY, name VARCHAR(160) NOT NULL, join_code VARCHAR(24) NOT NULL, owner_id INTEGER NOT NULL, created_at DATETIME NOT NULL);
    CREATE TABLE assignments (id INTEGER PRIMARY KEY, classroom_id INTEGER NOT NULL, title VARCHAR(200) NOT NULL, description TEXT NOT NULL, due_at DATETIME NOT NULL, status VARCHAR(20) NOT NULL, rubric_json TEXT NOT NULL, answer_key TEXT NOT NULL, dataset_json TEXT NOT NULL, created_at DATETIME NOT NULL);
    CREATE TABLE submissions (id INTEGER PRIMARY KEY, assignment_id INTEGER NOT NULL, student_id INTEGER NOT NULL, draft_markdown TEXT NOT NULL, shared BOOLEAN NOT NULL, grade_json TEXT, grade_published BOOLEAN NOT NULL, teacher_comment TEXT, updated_at DATETIME NOT NULL);
    CREATE TABLE submission_versions (id INTEGER PRIMARY KEY, submission_id INTEGER NOT NULL, version_number INTEGER NOT NULL, body_markdown TEXT NOT NULL, submitted_at DATETIME NOT NULL, review_json TEXT);
    CREATE TABLE ai_jobs (id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL, assignment_id INTEGER NOT NULL, submission_id INTEGER, version_id INTEGER, kind VARCHAR(24) NOT NULL, status VARCHAR(20) NOT NULL, prompt TEXT NOT NULL, result_json TEXT, error_message TEXT, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL);
    INSERT INTO users VALUES (1, 't@x.com', 'Teacher', 'x', 'teacher', '2024-01-01');
    INSERT INTO classrooms VALUES (1, 'Lop', 'CODE', 1, '2024-01-01');
    INSERT INTO assignments VALUES (1, 1, 'Bai cu', 'Mo ta', '2030-01-01', 'published', '[]', 'key', '[]', '2024-01-01');
    INSERT INTO submissions VALUES (1, 1, 1, 'draft', 0, NULL, 0, NULL, '2024-01-01');
    INSERT INTO submission_versions VALUES (1, 1, 1, 'body', '2024-01-01', NULL);
    """)
    conn.commit(); conn.close()
    # Run alembic against the legacy DB
    env = dict(os.environ)
    env["WEB02_DATABASE_URL"] = f"sqlite:///{legacy}"
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=str(Path(__file__).resolve().parents[1]), env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    conn = sqlite3.connect(str(legacy))
    version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    assert version == "0005_submission_votes"
    assert conn.execute("SELECT COUNT(*) FROM submission_votes").fetchone()[0] == 0
    columns = {row[1] for row in conn.execute("PRAGMA table_info(assignment_questions)")}
    assert "max_score" in columns
    # legacy data preserved, not auto-published
    assert conn.execute("SELECT COUNT(*) FROM assignments").fetchone()[0] == 1
    ref_published = conn.execute("SELECT reference_published FROM assignments WHERE id=1").fetchone()[0]
    assert ref_published == 0
    conn.close()

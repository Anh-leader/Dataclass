import json

from sqlalchemy import select
from test_questions import _clean_db, _make_teacher_class, _create_assignment, _login, _csrf, _join, client
from app.database import SessionLocal
from app.models import AIJob, Assignment


def setup_draft():
    class_id = _make_teacher_class()
    assignment_id = _create_assignment(class_id)
    response = client.post(f"/api/assignments/{assignment_id}/datasets", files=[("files", ("sales.csv", b"region,revenue\nNorth,10\nSouth,20\n", "text/csv"))], headers={"x-csrf-token": _csrf()})
    assert response.status_code == 200
    return class_id, assignment_id


def generate(assignment_id, **params):
    return client.post(f"/api/assignments/{assignment_id}/ai/generate-exam", json={"count": 2, **params}, headers={"x-csrf-token": _csrf()})


def complete_job(assignment_id):
    response = generate(assignment_id)
    assert response.status_code == 200, response.text
    job_id = response.json()["job_id"]
    with SessionLocal() as db:
        job = db.get(AIJob, job_id)
        job.status = "done"
        job.result_json = json.dumps({"questions": [{"question_order": 1, "question_text": "Tổng doanh thu?", "max_score": 10, "answer_markdown": "SECRET ANSWER: 30"}], "note": "", "evidence": "30", "artifacts": []})
        db.commit()
    return job_id


def apply(assignment_id, job_id, **params):
    return client.post(f"/api/assignments/{assignment_id}/ai/apply-exam", json={"job_id": job_id, "questions": [{"question_order": 1, "question_text": "Tổng doanh thu đã chỉnh?", "max_score": 5, "answer_markdown": "SECRET EDITED ANSWER: 30"}], **params}, headers={"x-csrf-token": _csrf()})


def test_ai_creation_allows_empty_draft_but_publish_requires_reviewed_questions():
    class_id = _make_teacher_class()
    response = client.post(f"/api/classes/{class_id}/assignments", json={"title": "AI draft", "due_at": "2030-01-01T00:00:00+07:00", "ai_generate": True, "questions": []}, headers={"x-csrf-token": _csrf()})
    assert response.status_code == 200, response.text
    aid = response.json()["id"]
    assert response.json()["questions"] == []
    assert generate(aid).status_code == 422
    client.post(f"/api/assignments/{aid}/datasets", files=[("files", ("a.csv", b"a\n1\n", "text/csv"))], headers={"x-csrf-token": _csrf()})
    assert client.post(f"/api/assignments/{aid}/publish", headers={"x-csrf-token": _csrf()}).status_code == 422


def test_generation_validates_settings_and_deduplicates_pending_jobs():
    _, aid = setup_draft()
    for settings in [{"count": 0}, {"count": True}, {"count": 2.5}, {"count": 21}, {"difficulty": "bad"}, {"instructions": "a" * 4001}]:
        assert generate(aid, **settings).status_code == 422
    first = generate(aid).json()
    assert generate(aid).json()["job_id"] == first["job_id"]
    assert client.get(f"/api/assignments/{aid}").json()["generation_job"]["id"] == first["job_id"]


def test_apply_saves_teacher_edits_and_keeps_answers_private():
    class_id, aid = setup_draft()
    job_id = complete_job(aid)
    response = apply(aid, job_id)
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["questions"]) == 1 and data["questions"][0]["max_score"] == 5
    assert "SECRET EDITED" in data["answer_key"]
    assert "SECRET EDITED" in data["reference"]["answers"][0]["answer_markdown"]
    assert data["reference"]["published"] is False
    saved_job = client.get(f"/api/jobs/{job_id}").json()
    assert saved_job["settings"]["count"] == 2
    assert saved_job["result"]["questions"][0]["question_text"] == "Tổng doanh thu đã chỉnh?"
    assert client.post(f"/api/assignments/{aid}/publish", headers={"x-csrf-token": _csrf()}).status_code == 200
    _join(class_id, "student@test.edu")
    data = client.get(f"/api/assignments/{aid}").json()
    assert "answer_key" not in data and "generation_job" not in data
    assert "SECRET" not in json.dumps(data)
    assert client.get(f"/api/jobs/{job_id}").status_code == 403
    assert client.get(f"/api/assignments/{aid}/reference").status_code == 404
    assert generate(aid).status_code == 403
    _login("teacher@test.edu")
    assert apply(aid, job_id).status_code == 409
    assert generate(aid).status_code == 409


def test_apply_rejects_stale_dataset_or_incomplete_answers_atomically():
    _, aid = setup_draft()
    job_id = complete_job(aid)
    before = client.get(f"/api/assignments/{aid}").json()
    assert apply(aid, job_id, questions=[{"question_order": 1, "question_text": "New", "answer_markdown": ""}]).status_code == 422
    assert client.get(f"/api/assignments/{aid}").json()["questions"] == before["questions"]
    client.post(f"/api/assignments/{aid}/datasets", files=[("files", ("extra.csv", b"x\n2\n", "text/csv"))], headers={"x-csrf-token": _csrf()})
    assert apply(aid, job_id).status_code == 409


def test_worker_generates_suggestion_without_changing_assignment(monkeypatch):
    _, aid = setup_draft()
    job_id = generate(aid).json()["job_id"]
    from app import worker
    seen = []
    def fake(context, files, job):
        seen.append((context, files, job))
        return {"questions": [{"question_order": 1, "question_text": "Generated", "max_score": 10, "answer_markdown": "30"}], "note": "", "evidence": "Verified 30", "artifacts": []}
    monkeypatch.setattr(worker, "generate_exam", fake)
    worker._execute(job_id)
    assert seen[0][0]["count"] == 2 and seen[0][1][0].endswith("sales.csv")
    assert client.get(f"/api/jobs/{job_id}").json()["status"] == "done"
    assert client.get(f"/api/assignments/{aid}").json()["questions"][0]["question_text"] == "Câu hỏi một là gì?"


def test_generated_charts_follow_reference_visibility_not_peer_sharing():
    from app.models import Artifact
    from app.config import ARTIFACT_DIR
    class_id, aid = setup_draft()
    job_id = complete_job(aid)
    with SessionLocal() as db:
        for artifact_id in ["reference-chart", "private-working"]:
            path = ARTIFACT_DIR / (artifact_id + ".png")
            path.write_bytes(b"chart")
            db.add(Artifact(id=artifact_id, job_id=job_id, local_path=str(path), display_name=path.name, media_type="image/png"))
        db.commit()
    answer = "30\n\n![Chart](/api/assets/reference-chart)"
    assert apply(aid, job_id, questions=[{"question_order": 1, "question_text": "Revenue?", "answer_markdown": answer}]).status_code == 200
    client.post(f"/api/assignments/{aid}/publish", headers={"x-csrf-token": _csrf()})
    _join(class_id, "student@test.edu")
    assert client.get("/api/assets/reference-chart").status_code == 403
    _login("teacher@test.edu")
    assert client.post(f"/api/assignments/{aid}/reference/publish", json={"published": True}, headers={"x-csrf-token": _csrf()}).status_code == 200
    _login("student@test.edu")
    assert client.get("/api/assets/reference-chart").status_code == 403
    qid = client.get(f"/api/assignments/{aid}").json()["questions"][0]["id"]
    client.put(f"/api/assignments/{aid}/answers", json={"answers": [{"question_id": qid, "answer_markdown": "30", "artifact_ids": []}]}, headers={"x-csrf-token": _csrf()})
    assert client.post(f"/api/assignments/{aid}/submit", json={}, headers={"x-csrf-token": _csrf()}).status_code == 200
    assert client.get("/api/assets/reference-chart").status_code == 200
    assert client.get("/api/assets/private-working").status_code == 403
    _login("teacher@test.edu")
    client.post(f"/api/assignments/{aid}/reference/publish", json={"published": False}, headers={"x-csrf-token": _csrf()})
    _login("student@test.edu")
    assert client.get("/api/assets/reference-chart").status_code == 403


def test_generation_uses_full_dataset_and_validates_answers(monkeypatch, tmp_path):
    from app import exam_generation
    import pytest
    path = tmp_path / "data.csv"
    path.write_text("amount\n" + "\n".join(str(n) for n in range(1, 21)))
    profile = json.loads(exam_generation.dataset_profile([str(path)]))[0]
    assert profile["rows"] == 20 and len(profile["preview_only"]) == 8
    assert profile["full_data_numeric_summary"]["amount"]["mean"] == 10.5
    class FakeLLM:
        def with_structured_output(self, schema):
            class Chain:
                def invoke(self, prompt):
                    if schema is exam_generation.ProposedExam:
                        return schema(questions=[{"question_text": "Tổng amount?"}])
                    return schema(answers=[{"question_order": 2, "answer_markdown": "Invalid order"}])
            return Chain()
    monkeypatch.setattr(exam_generation.ai_service, "_load_graph", lambda: (None, None, FakeLLM()))
    monkeypatch.setattr(exam_generation.ai_service, "run_graph", lambda *args: ("Tổng 210", []))
    with pytest.raises(ValueError, match="incomplete"):
        exam_generation.generate_exam({"count": 1, "difficulty": "easy", "instructions": "", "title": "Test", "description": ""}, [str(path)], 1)

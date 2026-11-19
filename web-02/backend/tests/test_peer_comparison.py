import json
from datetime import timedelta
import pytest
from sqlalchemy import select
from test_questions import _clean_db, client, _login, _csrf
from test_peer_learning import setup_assignment, submit, set_times
from app.database import SessionLocal
from app.models import Assignment, Submission, SubmissionVersion, AIJob, User, Membership, utcnow
from app import peer_comparison, worker


def prepare():
    class_id, assignment_id = setup_assignment()
    mine = submit(assignment_id)
    other = submit(assignment_id, "other@test.edu", "Bài bạn")
    # Simulate two on-time submissions followed by the deadline passing.
    with SessionLocal() as db:
        for item in (mine, other):
            db.get(SubmissionVersion, item["version_id"]).submitted_at = utcnow() - timedelta(days=2)
        db.commit()
    set_times(assignment_id)
    _login("student@test.edu")
    return class_id, assignment_id, mine, other


def compare(assignment_id, base, peers):
    return client.post(f"/api/assignments/{assignment_id}/ai/compare-submissions", json={
        "base_version_id": base, "peer_version_ids": peers}, headers={"x-csrf-token": _csrf()})


def test_schedule_identity_assignment_and_duplicate_sources():
    _, aid, mine, other = prepare()
    base, peer = mine["version_id"], other["version_id"]
    set_times(aid, sharing_in=1)
    assert compare(aid, base, [peer]).status_code == 409
    set_times(aid)
    assert compare(aid, peer, [base]).status_code == 404
    assert compare(aid, base, [base]).status_code == 422
    assert compare(aid, base, [peer, peer]).status_code == 422
    assert compare(aid, base, []).status_code == 422
    with SessionLocal() as db:
        current = db.get(Assignment, aid)
        second = Assignment(classroom_id=current.classroom_id, title="Other dataset", due_at=current.due_at)
        db.add(second); db.flush()
        db.get(Submission, other["submission_id"]).assignment_id = second.id
        db.commit()
    assert compare(aid, base, [peer]).status_code == 404


def test_frozen_context_private_key_dedup_and_revoked_access():
    _, aid, mine, other = prepare()
    with SessionLocal() as db:
        db.get(Assignment, aid).answer_key = "PRIVATE_KEY_SENTINEL"
        db.get(Submission, other["submission_id"]).draft_markdown = "PRIVATE_DRAFT_SENTINEL"
        db.commit()
    first = compare(aid, mine["version_id"], [other["version_id"]])
    assert first.status_code == 200, first.text
    job_id = first.json()["job_id"]
    assert compare(aid, mine["version_id"], [other["version_id"]]).json()["job_id"] == job_id
    with SessionLocal() as db:
        job = db.get(AIJob, job_id)
        assert "Bài bạn" in job.prompt
        assert "PRIVATE_KEY_SENTINEL" not in job.prompt and "PRIVATE_DRAFT_SENTINEL" not in job.prompt
        job.status = "done"; job.result_json = '{"summary":"SAVED_FEEDBACK"}'
        db.commit()
    assert compare(aid, mine["version_id"], [other["version_id"]]).json()["job_id"] == job_id
    _login("other@test.edu")
    assert client.get(f"/api/jobs/{job_id}").status_code == 403
    _login("student@test.edu")
    assert "SAVED_FEEDBACK" in client.get(f"/api/assignments/{aid}/ai/comparisons").text
    set_times(aid, mode="opt_in")
    with SessionLocal() as db:
        db.get(Submission, other["submission_id"]).shared = False; db.commit()
    assert client.get(f"/api/jobs/{job_id}").status_code == 404
    assert client.get(f"/api/assignments/{aid}/ai/comparisons").json()["history"] == []
    assert compare(aid, mine["version_id"], [other["version_id"]]).status_code == 404
    set_times(aid, sharing_in=1)
    assert client.get(f"/api/jobs/{job_id}").status_code == 409


def test_teacher_and_membership_and_unshared_own_source():
    cid, aid, mine, other = prepare()
    set_times(aid, mode="opt_in")
    with SessionLocal() as db:
        db.get(Submission, mine["submission_id"]).shared = False
        db.get(Submission, other["submission_id"]).shared = True; db.commit()
    sources = client.get(f"/api/assignments/{aid}/ai/comparisons").json()["sources"]
    assert any(s["is_mine"] for s in sources)
    assert compare(aid, mine["version_id"], [other["version_id"]]).status_code == 200
    _login("teacher@test.edu")
    assert compare(aid, other["version_id"], [mine["version_id"]]).status_code == 404
    set_times(aid, mode="all")
    assert compare(aid, other["version_id"], [mine["version_id"]]).status_code == 200
    with SessionLocal() as db:
        student = db.scalar(select(User).where(User.email == "student@test.edu"))
        membership = db.scalar(select(Membership).where(Membership.user_id == student.id, Membership.classroom_id == cid))
        db.delete(membership); db.commit()
    _login("student@test.edu")
    assert client.get(f"/api/assignments/{aid}/ai/comparisons").status_code == 403


def test_worker_single_call_validated_references_no_review_overwrite(monkeypatch):
    _, aid, mine, other = prepare()
    job_id = compare(aid, mine["version_id"], [other["version_id"]]).json()["job_id"]
    calls = []
    class FakeLLM:
        def with_structured_output(self, schema):
            assert schema is peer_comparison.ComparisonFeedback
            return self
        def invoke(self, prompt):
            calls.append(prompt)
            with SessionLocal() as db:
                context = json.loads(db.get(AIJob, job_id).prompt)
            return peer_comparison.ComparisonFeedback(summary="Khác biệt cụ thể", next_steps=["Bổ sung đơn vị"], questions=[
                peer_comparison.QuestionComparison(question_id=q["id"], base_strengths="Có phương pháp", base_gaps="Thiếu đơn vị",
                    peers=[peer_comparison.PeerDifference(version_id=other["version_id"], similarities="Cùng tổng hợp", differences="Dùng tỷ suất", learn_from_peer="Học cách tính tỷ suất")]) for q in context["questions"]])
    monkeypatch.setattr(peer_comparison, "_load_graph", lambda: (None, None, FakeLLM()))
    monkeypatch.setattr(worker, "_files", lambda _: pytest.fail("Comparison must not run dataset graph"))
    with SessionLocal() as db:
        old_review = db.get(SubmissionVersion, mine["version_id"]).review_json
    worker._execute(job_id)
    assert len(calls) == 1
    with SessionLocal() as db:
        job = db.get(AIJob, job_id)
        assert job.status == "done"
        assert db.get(SubmissionVersion, mine["version_id"]).review_json == old_review
        result = json.loads(job.result_json)
        assert result["sources"]["peers"][0]["version_id"] == other["version_id"]
        context = json.loads(job.prompt)
    original = FakeLLM.invoke
    def invalid(self, prompt):
        feedback = original(self, prompt); feedback.questions[0].peers[0].version_id = 999999; return feedback
    monkeypatch.setattr(FakeLLM, "invoke", invalid)
    with pytest.raises(RuntimeError, match="peer references"):
        peer_comparison.compare_reports(context)


def test_extended_demo_is_additive_and_idempotent(tmp_path, monkeypatch):
    from app import seed_demo, seed_comparison_demo
    monkeypatch.setattr(seed_demo, "BASE_DIR", tmp_path)
    seed_demo.main()
    with SessionLocal() as db:
        original = {a.id: (a.title, a.answer_key) for a in db.scalars(select(Assignment)).all()}
    manifest = seed_comparison_demo.main()
    assert seed_comparison_demo.main() == manifest
    with SessionLocal() as db:
        for aid, values in original.items():
            assert (db.get(Assignment, aid).title, db.get(Assignment, aid).answer_key) == values
        jobs = db.scalars(select(AIJob).where(AIJob.kind == "peer_comparison")).all()
        assert len(jobs) == 6 and all(json.loads(j.result_json)["demo"] for j in jobs)
        versions = db.scalars(select(SubmissionVersion).join(Submission).where(Submission.assignment_id == manifest["assignment_id"])).all()
        assert len(versions) == 6
        assert any("40%" in v.body_markdown for v in versions)
        assert any("chưa kiểm tra tốc độ" in v.body_markdown for v in versions)

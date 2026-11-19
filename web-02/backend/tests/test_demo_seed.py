import json
from sqlalchemy import select, func
from test_questions import _clean_db, _make_teacher_class
from app.database import SessionLocal
from app.models import User, Classroom, Assignment, Submission, SubmissionVersion, PeerReview, Artifact, AIJob


def test_demo_seed_preserves_existing_data_and_does_not_duplicate(tmp_path, monkeypatch):
    class_id = _make_teacher_class()
    from app import seed_demo
    monkeypatch.setattr(seed_demo, "BASE_DIR", tmp_path)
    with SessionLocal() as db:
        old_user = db.scalar(select(User).where(User.email == "teacher@test.edu"))
        old_hash = old_user.password_hash
    seed_demo.main()
    with SessionLocal() as db:
        counts = [db.scalar(select(func.count()).select_from(model)) for model in [User, Classroom, Assignment, Submission, SubmissionVersion, PeerReview, Artifact, AIJob]]
        assert counts[:7] == [9, 3, 4, 12, 9, 5, 12]
        assert db.get(Classroom, class_id).name == "Test Class"
        assert db.scalar(select(User).where(User.email == "teacher@test.edu")).password_hash == old_hash
        improved = db.scalar(select(SubmissionVersion).where(SubmissionVersion.is_improvement == True))
        assert improved.reflection and improved.grade_json is None
        original = db.scalar(select(SubmissionVersion).where(SubmissionVersion.submission_id == improved.submission_id, SubmissionVersion.version_number == 1))
        assert original.grade_published and original.grade_json
        for job in db.scalars(select(AIJob)).all():
            assert job.status == "done" and "DỮ LIỆU MẪU" in job.prompt
        for assignment in db.scalars(select(Assignment)).all():
            for dataset in json.loads(assignment.dataset_json):
                assert seed_demo.Path(dataset["path"]).is_file()
    seed_demo.main()
    with SessionLocal() as db:
        assert counts == [db.scalar(select(func.count()).select_from(model)) for model in [User, Classroom, Assignment, Submission, SubmissionVersion, PeerReview, Artifact, AIJob]]

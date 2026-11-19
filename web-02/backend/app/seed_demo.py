"""Add an idempotent demo classroom without modifying existing users or classes.

Run after migrations: python -m app.seed_demo
"""
import csv
import json
import random
import shutil
import sqlite3
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import select

from .config import BASE_DIR, DATA_DIR, UPLOAD_DIR, ARTIFACT_DIR
from .database import SessionLocal, engine
from .models import User, Classroom, Membership, Assignment, AssignmentQuestion, Submission, SubmissionAnswer, SubmissionVersion, AIJob, Artifact, PeerReview, Comment, utcnow
from .security import hash_password

PASSWORD = "Demo@2026!"
TEACHER_EMAIL = "giaovien.demo@dataclass.local"
STUDENT_EMAILS = [f"sinhvien{i}.demo@dataclass.local" for i in range(1, 6)]


def markdown_table(frame):
    rows = frame.reset_index()
    def cell(value):
        return f"{value:.2f}" if isinstance(value, float) else str(value)
    return "\n".join(["| " + " | ".join(map(str, rows.columns)) + " |", "| " + " | ".join("---" for _ in rows.columns) + " |", *["| " + " | ".join(cell(x) for x in row) + " |" for row in rows.itertuples(index=False, name=None)]])


def write_datasets():
    target = BASE_DIR / "demo" / "datasets"
    target.mkdir(parents=True, exist_ok=True)
    retail = target / "retail_sales.csv"
    with retail.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "month", "region", "channel", "product", "units", "unit_price", "revenue", "cost", "profit"])
        rng = random.Random(2026)
        for i in range(180):
            units = rng.randint(2, 25)
            price = [120000, 250000, 450000][i % 3]
            revenue = units * price
            cost = int(revenue * [0.6, 0.68, 0.72][i % 3])
            writer.writerow([f"DH{i+1:04}", f"2026-{i//30+1:02}", ["Bắc", "Trung", "Nam"][i % 3], ["Online", "Cửa hàng"][i % 2], ["Sách", "Tai nghe", "Bàn phím"][i % 3], units, price, revenue, cost, revenue - cost])
    education = target / "student_learning.csv"
    with education.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["student_code", "group", "study_hours_week", "attendance_pct", "assignment_score", "exam_score"])
        rng = random.Random(71)
        for i in range(80):
            hours = rng.randint(3, 20)
            attendance = rng.randint(65, 100)
            score = round(min(10, max(0, 2 + hours * .2 + attendance * .025 + rng.uniform(-2, 1))), 1)
            writer.writerow([f"SV{i+1:03}", ["A", "B"][i % 2], hours, attendance, round(min(10, score + rng.uniform(-1, 1)), 1), score])
    return retail, education


def assessment_data(path):
    frame = pd.read_csv(path)
    if "revenue" in frame:
        region = frame.groupby("region")[["revenue", "profit"]].sum().sort_values("revenue", ascending=False)
        months = frame.groupby("month")["revenue"].sum()
        top = region.index[0]
        total = int(frame.revenue.sum())
        questions = ["Khám phá cấu trúc dataset, kiểm tra giá trị thiếu và tính tổng doanh thu, tổng lợi nhuận. Đơn vị tiền là VND.",
                     "So sánh doanh thu và lợi nhuận theo vùng. Vẽ biểu đồ và xác định vùng đóng góp doanh thu lớn nhất, kèm tỷ trọng.",
                     "Phân tích doanh thu theo tháng; đưa ra hai insight, một đề xuất kinh doanh và giới hạn của kết luận."]
        answers = [f"Dataset có {len(frame)} dòng, {len(frame.columns)} cột; không có giá trị thiếu. Tổng doanh thu **{total:,} VND**, tổng lợi nhuận **{int(frame.profit.sum()):,} VND**. Doanh thu = units × unit_price, lợi nhuận = revenue − cost.",
                   "Nhóm theo region rồi cộng revenue và profit:\n\n" + markdown_table(region) + f"\n\nVùng {top} đứng đầu doanh thu, chiếm **{region.iloc[0].revenue / total * 100:.2f}%** tổng doanh thu. Cần so sánh cả quy mô và tỷ suất, không chỉ doanh thu.",
                   "Doanh thu theo tháng:\n\n" + markdown_table(months.to_frame()) + f"\n\nTháng {months.idxmax()} có doanh thu cao nhất. Có thể ưu tiên tìm hiểu cơ cấu sản phẩm tại vùng {top} và nhu cầu tháng cao điểm trước khi thử điều chỉnh tồn kho. Dữ liệu giả lập chỉ có 6 tháng, mỗi vùng gắn với một loại sản phẩm nên cơ cấu giá có thể chi phối chênh lệch; không có marketing hay dữ liệu khách hàng. Không kết luận quan hệ nhân quả hoặc mùa vụ dài hạn."]
        return frame, questions, answers, region["revenue"], "Doanh thu theo vùng (VND)"
    correlation = frame.study_hours_week.corr(frame.exam_score)
    groups = frame.groupby("group")[["exam_score", "assignment_score"]].mean().round(2)
    questions = ["Mô tả dataset và tính điểm thi trung bình, trung vị, số sinh viên; kiểm tra giá trị thiếu.",
                 "So sánh điểm thi trung bình theo nhóm A/B bằng bảng và biểu đồ. Phân biệt chênh lệch quan sát với kết luận về chất lượng nhóm.",
                 "Tính tương quan giữa số giờ tự học và điểm thi. Đưa ra insight, một đề xuất hỗ trợ sinh viên và giới hạn khi suy luận."]
    answers = [f"Có {len(frame)} sinh viên giả lập, {len(frame.columns)} cột và không có giá trị thiếu. Điểm thi trung bình **{frame.exam_score.mean():.2f}/10**, trung vị **{frame.exam_score.median():.2f}/10**. Kiểm tra bằng count, isna, mean và median.",
               "Nhóm theo group và lấy trung bình:\n\n" + markdown_table(groups) + "\n\nChênh lệch này chỉ mô tả mẫu hiện có. Chưa đủ cơ sở kết luận một nhóm học tốt hơn trong quần thể khi chưa kiểm tra phân bố, yếu tố nền và độ bất định.",
               f"Tương quan Pearson giữa study_hours_week và exam_score là **{correlation:.3f}**. Dùng corr trên toàn bộ 80 dòng. Có thể hỗ trợ lập lịch tự học và theo dõi tiến bộ. Tương quan không chứng minh học thêm giờ gây tăng điểm; còn yếu tố nền, độ khó và sai lệch tự báo cáo. Đây là dữ liệu giả lập."]
    return frame, questions, answers, groups["exam_score"], "Điểm thi trung bình theo nhóm"


def add_assignment(db, classroom, title, source, *, closed=False, draft=False, opt_in=False):
    now = utcnow()
    a = Assignment(classroom_id=classroom.id, title=title, description="[DỮ LIỆU MẪU] Thực hành phân tích dataset giả lập. Trình bày cách tính, bảng hoặc biểu đồ, insight và giới hạn. Sinh viên tự viết câu trả lời; AI hỗ trợ gợi ý.",
                   due_at=now + timedelta(days=-1 if closed else 7), sharing_open_at=now + timedelta(days=-1 if closed else 8),
                   status="draft" if draft else "published", share_mode="opt_in" if opt_in else "all", allow_improvements=True,
                   rubric_json=json.dumps([{"id": "accuracy", "title": "Tính chính xác", "description": "Số liệu đúng và có cách tính", "max_points": 4}, {"id": "insight", "title": "Insight và bằng chứng", "description": "Lập luận có bảng, biểu đồ", "max_points": 4}, {"id": "limits", "title": "Giới hạn kết luận", "description": "Không suy luận vượt dữ liệu", "max_points": 2}], ensure_ascii=False) if closed else "[]")
    db.add(a); db.flush()
    directory = UPLOAD_DIR / f"assignment-{a.id}"
    directory.mkdir(exist_ok=True)
    copy = directory / f"demo-{source.name}"
    shutil.copy2(source, copy)
    a.dataset_json = json.dumps([{"id": uuid4().hex, "name": source.name, "size": copy.stat().st_size, "path": str(copy.resolve())}], ensure_ascii=False)
    _, texts, answers, series, chart_title = assessment_data(source)
    if draft:
        return a, [], answers, series, chart_title
    questions = []
    for order, text in enumerate(texts, 1):
        q = AssignmentQuestion(assignment_id=a.id, question_order=order, question_text=text, max_score=10)
        db.add(q); db.flush(); questions.append(q)
    a.answer_key = "\n\n".join(f"Câu {i+1}\n{x}" for i, x in enumerate(answers))
    a.reference_answer_json = json.dumps({"answers": [{"question_id": q.id, "question_order": q.question_order, "answer_markdown": answer, "artifact_ids": []} for q, answer in zip(questions, answers)], "note": "Đáp án tính từ dataset giả lập bằng pandas. Đây là bài minh họa.", "artifacts": []}, ensure_ascii=False)
    a.reference_published = closed
    return a, questions, answers, series, chart_title


def add_submission(db, a, questions, references, series, chart_title, student, index, *, submitted=True, improved=False, graded=False, partial_answer=True):
    now = utcnow()
    submission = Submission(assignment_id=a.id, student_id=student.id, shared=index != 4)
    db.add(submission); db.flush()
    chart_path = ARTIFACT_DIR / f"demo-{a.id}-{student.id}.png"
    fig, ax = plt.subplots(figsize=(7, 4))
    series.plot.bar(ax=ax, color=["#1c7268", "#3d9e90", "#91c7bd"][:len(series)])
    ax.set_title(chart_title); ax.set_xlabel(""); ax.tick_params(axis="x", rotation=0)
    fig.tight_layout(); fig.savefig(chart_path, dpi=120); plt.close(fig)
    artifact_id = uuid4().hex
    artifact_view = {"id": artifact_id, "name": chart_path.name, "media_type": "image/png", "url": f"/api/assets/{artifact_id}"}
    chat = AIJob(owner_id=student.id, assignment_id=a.id, question_id=questions[1].id, kind="chat", status="done",
                 prompt="[DỮ LIỆU MẪU] Minh họa biểu đồ nhóm; được tạo bằng script seed, không phải cuộc gọi AI.",
                 result_json=json.dumps({"answer": "[DỮ LIỆU MẪU] Dùng groupby để tính thống kê theo nhóm. Kiểm tra đơn vị và giới hạn trước khi diễn giải.\n\n" + f"![Biểu đồ](/api/assets/{artifact_id})", "artifacts": [artifact_view]}, ensure_ascii=False))
    db.add(chat); db.flush()
    db.add(Artifact(id=artifact_id, job_id=chat.id, local_path=str(chart_path.resolve()), display_name=chart_path.name, media_type="image/png"))
    values = []
    for i, answer in enumerate(references):
        prefix = ["Tôi kiểm tra số liệu trước khi kết luận.", "Tôi tập trung so sánh giữa các nhóm.", "Tôi trình bày kết quả bằng bảng và diễn giải.", "Tôi đang bổ sung cách tính để kiểm chứng insight.", "Tôi ưu tiên nêu giới hạn của dữ liệu."][index]
        text = prefix + "\n\n" + answer
        if partial_answer and index == 3 and i == 2:
            text = "Dữ liệu có khác biệt giữa các nhóm. Tôi cần tính thêm các chỉ số để củng cố nhận định. Chưa có đủ bằng chứng cho đề xuất cụ thể."
        values.append(text)
    snapshot = [{"question_id": q.id, "question_order": q.question_order, "question_text": q.question_text, "answer_markdown": values[i], "artifacts": [artifact_view] if i == 1 else [], "updated_at": now.isoformat()} for i, q in enumerate(questions)]
    def body(entries):
        return "\n\n".join(f"## Câu hỏi {x['question_order']}\n\n{x['question_text']}\n\n{x['answer_markdown']}" + (f"\n\n![Biểu đồ](/api/assets/{artifact_id})" if x["artifacts"] else "") for x in entries)
    versions = []
    for number in range(1, (2 if improved else 1) + 1 if submitted else 1):
        entries = json.loads(json.dumps(snapshot))
        if number == 2:
            entries[2]["answer_markdown"] += "\n\nSau khi đọc bài của bạn, tôi phân biệt chênh lệch quan sát với nguyên nhân và bổ sung giới hạn của đề xuất."
        review = {"checks": [{"question_id": q.id, "question_order": q.question_order, "status": "partial" if index == 3 else "met", "feedback": "[DỮ LIỆU MẪU] Bổ sung phương pháp và đối chiếu số liệu.", "suggestion": "Kiểm tra giới hạn và thêm bằng chứng."} for q in questions], "overall": {"quality": "partial" if index == 3 else "good", "feedback": "[DỮ LIỆU MẪU] Phản hồi minh họa được tạo bằng seed, không phải kết quả chấm AI thật.", "suggestion": "Tiếp tục kiểm chứng số liệu và giới hạn."}}
        grade = {"total": 24 if index != 3 else 18, "max_score": 30, "per_question": [{"question_id": q.id, "question_order": q.question_order, "score": 8 if index != 3 else 6, "max_score": 10, "feedback": "Điểm minh họa cho dữ liệu mẫu."} for q in questions]}
        version = SubmissionVersion(submission_id=submission.id, version_number=number, body_markdown=body(entries), answers_snapshot_json=json.dumps(entries, ensure_ascii=False),
                                    submitted_at=now - timedelta(days=2) if number == 1 else now - timedelta(hours=2), review_json=json.dumps(review, ensure_ascii=False),
                                    is_improvement=number == 2, reflection="Tôi học được cách ghi rõ phương pháp và giới hạn từ bài của bạn." if number == 2 else "",
                                    grade_json=json.dumps(grade, ensure_ascii=False) if graded and number == 1 else None, grade_published=graded and number == 1,
                                    teacher_comment="[DỮ LIỆU MẪU] Trình bày rõ, tiếp tục bổ sung giới hạn." if graded and number == 1 else None)
        db.add(version); db.flush(); versions.append(version)
        db.add(AIJob(owner_id=student.id, assignment_id=a.id, submission_id=submission.id, version_id=version.id, kind="submitted_review", status="done",
                     prompt="[DỮ LIỆU MẪU] Phản hồi minh họa do script seed tạo.", result_json=json.dumps({**review, "artifacts": []}, ensure_ascii=False)))
        if number == 2: snapshot = entries
    for i, q in enumerate(questions):
        db.add(SubmissionAnswer(submission_id=submission.id, question_id=q.id, answer_markdown=snapshot[i]["answer_markdown"], selected_artifacts_json=json.dumps([artifact_id] if i == 1 else [])))
    submission.draft_markdown = body(snapshot)
    if versions:
        latest = versions[-1]
        submission.grade_json, submission.grade_published, submission.teacher_comment = latest.grade_json, latest.grade_published, latest.teacher_comment
    return submission, versions


def main():
    manifest_path = DATA_DIR / "demo-seed.json"
    with SessionLocal() as db:
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if all(db.get(Assignment, i) for i in manifest["assignment_ids"]):
                print("Demo data already exists; kept all demo work unchanged.")
                return
        if db.scalar(select(User.id).where(User.email.in_([TEACHER_EMAIL, *STUDENT_EMAILS]))) or db.scalar(select(Classroom.id).where(Classroom.join_code.in_(["DADEMO26", "STATDEMO26"]))):
            raise RuntimeError("Demo identifiers already exist without a valid seed manifest; refusing to overwrite.")
    if engine.url.get_backend_name() == "sqlite":
        backup = DATA_DIR / "backups" / f"before-demo-{utcnow():%Y%m%d-%H%M%S}.sqlite3"
        backup.parent.mkdir(exist_ok=True)
        with sqlite3.connect(engine.url.database) as original, sqlite3.connect(backup) as destination:
            original.backup(destination)
    retail, education = write_datasets()
    with SessionLocal.begin() as db:
        teacher = User(email=TEACHER_EMAIL, full_name="Giáo viên Demo", role="teacher", password_hash=hash_password(PASSWORD))
        db.add(teacher); db.flush()
        names = ["Nguyễn Minh Anh", "Trần Quốc Bảo", "Lê Thu Chi", "Phạm Hải Dương", "Võ Ngọc Hà"]
        students = []
        for email, name in zip(STUDENT_EMAILS, names):
            user = User(email=email, full_name=name + " (Demo)", role="student", password_hash=hash_password(PASSWORD))
            db.add(user); db.flush(); students.append(user)
        classes = []
        for name, code in [("[Demo] Phân tích dữ liệu kinh doanh", "DADEMO26"), ("[Demo] Thống kê và học từ dữ liệu", "STATDEMO26")]:
            classroom = Classroom(name=name, join_code=code, owner_id=teacher.id)
            db.add(classroom); db.flush(); classes.append(classroom)
            for student in students:
                db.add(Membership(classroom_id=classroom.id, user_id=student.id))
        specs = [(classes[0], "[Demo] Doanh thu bán lẻ — đang làm", retail, {}),
                 (classes[0], "[Demo] Doanh thu bán lẻ — chia sẻ và cải thiện", retail, {"closed": True}),
                 (classes[1], "[Demo] Kết quả học tập — chờ mở chia sẻ", education, {"opt_in": True}),
                 (classes[1], "[Demo] Soạn đề kiểm tra bằng AI", education, {"draft": True})]
        assignments = []
        for spec_index, (classroom, title, source, options) in enumerate(specs):
            a, questions, references, series, chart_title = add_assignment(db, classroom, title, source, **options)
            assignments.append(a)
            if options.get("draft"): continue
            submissions = []
            for i, student in enumerate(students):
                if spec_index == 2 and i > 2 or spec_index == 0 and i > 3: continue
                submitted = spec_index == 1 or spec_index == 0 and i < 2 or spec_index == 2 and i == 0
                submissions.append(add_submission(db, a, questions, references, series, chart_title, student, i, submitted=submitted, improved=spec_index == 1 and i == 0, graded=submitted and i < 2))
            if spec_index == 1:
                for i, (submission, versions) in enumerate(submissions):
                    reviewer = students[(i + 1) % len(students)]
                    db.add(PeerReview(version_id=versions[0].id, reviewer_id=reviewer.id, rating=3 if i == 3 else 5,
                                      strengths="Bảng so sánh và biểu đồ giúp tôi nhìn rõ khác biệt giữa các nhóm.", suggestions="Bổ sung đơn vị và giải thích giới hạn của kết luận.", learned="Tôi học được cách tính tỷ trọng, so sánh lợi nhuận và nêu giới hạn dữ liệu."))
                    db.add(Comment(submission_id=submission.id, author_id=reviewer.id, body="[Dữ liệu mẫu] Cách nhóm dữ liệu này rất hữu ích. Bạn có thể chia sẻ thêm cách kiểm tra tỷ trọng không?"))
        manifest = {"teacher_email": TEACHER_EMAIL, "student_emails": STUDENT_EMAILS, "class_ids": [c.id for c in classes], "assignment_ids": [a.id for a in assignments], "created_at": utcnow().isoformat()}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"added": {"teachers": 1, "students": 5, "classes": 2, "assignments": 4}, "manifest": str(manifest_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

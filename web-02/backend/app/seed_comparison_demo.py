"""Extend the existing demo additively: python -m app.seed_comparison_demo."""
import json
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import select

from .config import DATA_DIR
from .database import SessionLocal, engine
from .models import User, Classroom, Assignment, AIJob, Artifact, PeerReview, Comment, utcnow
from .seed_demo import TEACHER_EMAIL, STUDENT_EMAILS, add_assignment, add_submission, markdown_table
from .peer_comparison import build_comparison_context, deadline_version

TITLE = "[Demo khách] So sánh 5 cách phân tích doanh thu"
STYLES = ["kiểm tra và tổng hợp số liệu", "so sánh tỷ suất lợi nhuận", "trực quan hóa tỷ trọng doanh thu",
          "nhận xét định tính, còn thiếu bằng chứng", "phân tích cơ cấu sản phẩm và giới hạn"]


def report_answers(frame, index):
    total, profit = int(frame.revenue.sum()), int(frame.profit.sum())
    region = frame.groupby("region")[["revenue", "profit"]].sum().sort_values("revenue", ascending=False)
    region["Tỷ trọng (%)"] = region.revenue / total * 100
    region["Biên lợi nhuận (%)"] = region.profit / region.revenue * 100
    months = frame.groupby("month").revenue.sum()
    first = f"Kiểm tra `shape`, `isna().sum()` và `duplicated()` trên 180 dòng, 10 cột: không thiếu và không trùng cả dòng.\n\nTổng doanh thu **{total:,} VND**, lợi nhuận **{profit:,} VND**.\n\n$$\nR=\\sum_i q_i p_i,\\quad P=\\sum_i (R_i-C_i)\n$$"
    second = [
        markdown_table(region[["revenue", "profit"]]) + "\n\nNam có quy mô doanh thu lớn nhất. Tôi dùng tổng doanh thu làm thước đo quy mô và chưa so sánh tỷ suất giữa các vùng.",
        markdown_table(region[["profit", "Biên lợi nhuận (%)"]]) + "\n\nTỷ suất lợi nhuận Bắc **40%**, Trung **32%**, Nam **28%**. Nam dẫn đầu doanh thu nhưng Bắc có tỷ suất cao hơn.\n\n$M=P/R\\times100\\%$. Cần xem cả quy mô và tỷ suất trước khi phân bổ nguồn lực.",
        markdown_table(region[["revenue", "Tỷ trọng (%)"]]) + "\n\nDùng biểu đồ tròn để thấy đóng góp doanh thu: tổng tỷ trọng bằng 100%. Biểu đồ này chưa thể hiện lợi nhuận hoặc biến động theo tháng.",
        "Vùng Nam có vẻ bán hàng tốt nhất. Tôi chưa tính tỷ trọng hay tỷ suất lợi nhuận nên cần bổ sung bảng kiểm chứng trước khi đưa ra đề xuất.",
        markdown_table(region) + "\n\nMỗi vùng trong dữ liệu gắn với một loại sản phẩm (Bắc–Sách, Trung–Tai nghe, Nam–Bàn phím). Chênh lệch có thể do đơn giá và cơ cấu sản phẩm; không đủ cơ sở khẳng định vị trí địa lý tạo ra hiệu quả cao hơn.",
    ][index]
    third = markdown_table(months.to_frame("Doanh thu (VND)")) + f"\n\nTháng **{months.idxmax()}** cao nhất; tháng **{months.idxmin()}** thấp nhất. "
    third += [
        "Đề xuất kiểm tra nhu cầu tháng cao điểm và thử tăng tồn kho có theo dõi hiệu quả. Chưa tính tốc độ tăng giảm từng tháng; mẫu chỉ có sáu tháng nên chưa kết luận mùa vụ.",
        "Đề xuất theo dõi cả doanh thu lẫn biên lợi nhuận khi thử thay đổi hàng tồn kho. Lợi nhuận cao theo tỷ suất không đồng nghĩa tổng lợi nhuận lớn nhất; chưa có dữ liệu chi phí marketing.",
        "Hai insight là đóng góp doanh thu giữa vùng khác nhau và doanh thu giữa tháng khác nhau. Thử dashboard theo dõi tỷ trọng và xu hướng; cần thêm dữ liệu trước khi dự báo.",
        "Tôi nghĩ doanh thu sẽ luôn tăng và nên tăng hàng tồn kho cho mọi vùng. Tôi chưa kiểm tra tốc độ tăng giảm, nên đề xuất này cần được xem lại.",
        "Hai insight: quy mô doanh thu khác biệt cùng với giá sản phẩm; sáu tháng có biến động nhưng chưa chứng minh mùa vụ. Đề xuất thu thập thêm lịch sử, chi phí và phân nhóm sản phẩm để thử nghiệm nhỏ, thay vì kết luận nhân quả.",
    ][index]
    if index == 3:
        first = "Tôi đã mở CSV và quan sát dữ liệu bán hàng. Chưa tính đầy đủ tổng doanh thu và tổng lợi nhuận; cần bổ sung cách tính và đơn vị."
    return [first, second, third], region


def sample_comparison(context):
    base_index = STUDENT_EMAILS.index(context["base"]["email"]) if "email" in context["base"] else 0
    return {"demo": True,
            "summary": "**[DỮ LIỆU MẪU]** Các bài cùng dùng dataset bán lẻ nhưng khác cách đặt trọng tâm: quy mô, tỷ suất, tỷ trọng và giới hạn suy luận. Hãy học phương pháp phù hợp rồi tự kiểm chứng số liệu; không sao chép kết luận.",
            "questions": [{"question_id": q["id"],
                "base_strengths": f"Bài gốc có hướng tiếp cận {STYLES[base_index]}. Đối chiếu cách tính với yêu cầu câu hỏi để giữ phần lập luận phù hợp.",
                "base_gaps": ["Bổ sung kiểm tra trùng mã đơn hàng và ghi rõ đơn vị tiền.", "So sánh đồng thời tỷ trọng, tổng lợi nhuận và biên lợi nhuận; giải thích ảnh hưởng của cơ cấu sản phẩm.", "Đưa ra một thử nghiệm nhỏ có chỉ số theo dõi thay vì suy ra xu hướng dài hạn từ sáu tháng."][q["order"] - 1],
                "peers": [{"version_id": p["version_id"],
                    "similarities": "Cùng trả lời câu hỏi trên dataset bán lẻ và dùng vùng/tháng để mô tả kết quả.",
                    "differences": f"Bài của {p['student']} chú trọng {p['style']}. So sánh phần phương pháp và mức độ bằng chứng thay vì chỉ nhìn kết luận.",
                    "learn_from_peer": {1: "Học cách công khai các bước kiểm tra và công thức, rồi tự tính lại tổng để đối chiếu.",
                                       2: f"Thử bổ sung góc nhìn {p['style']}. Với tỷ suất, dùng $M=P/R\\times100\\%$; phân biệt quy mô doanh thu với hiệu quả lợi nhuận.",
                                       3: "Ghi rõ giới hạn về cơ cấu sản phẩm và thời gian quan sát; nếu bài bạn thiếu bằng chứng, nhận ra phần đó cũng cần kiểm chứng."}[q["order"]]}
                    for p in context["peers"]]} for q in context["questions"]],
            "next_steps": ["Tự tính lại bảng tổng hợp, ghi đơn vị và công thức.", "Bổ sung tỷ suất hoặc tỷ trọng và giải thích ảnh hưởng của cơ cấu sản phẩm.", "Viết giới hạn của đề xuất và lưu bản cải thiện kèm điều đã học từ bạn."],
            "sources": {"base": {k: context["base"][k] for k in ("student", "version_id", "version_number")},
                        "peers": [{k: p[k] for k in ("student", "version_id", "version_number")} for p in context["peers"]]},
            "question_labels": context["questions"],
            "note": "DỮ LIỆU MẪU: nhận xét minh họa do script tạo để demo ngay, không phải kết quả gọi AI. Nhận xét AI thật cũng chỉ dựa trên báo cáo, không phải điểm giáo viên."}


def main():
    manifest_path = DATA_DIR / "demo-comparison.json"
    with SessionLocal() as db:
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if db.get(Assignment, manifest["assignment_id"]):
                print("Comparison demo already exists; preserved all work.")
                return manifest
        if db.scalar(select(Assignment.id).where(Assignment.title == TITLE)):
            raise RuntimeError("Demo exists without a manifest; refusing to duplicate or overwrite it")
        classroom = db.scalar(select(Classroom).where(Classroom.join_code == "DADEMO26"))
        if not classroom:
            raise RuntimeError("Run python -m app.seed_demo first")
    if engine.url.get_backend_name() == "sqlite":
        backup = DATA_DIR / "backups" / f"before-comparison-demo-{utcnow():%Y%m%d-%H%M%S}.sqlite3"
        backup.parent.mkdir(exist_ok=True)
        with sqlite3.connect(engine.url.database) as original, sqlite3.connect(backup) as destination:
            original.backup(destination)
    with SessionLocal.begin() as db:
        teacher = db.scalar(select(User).where(User.email == TEACHER_EMAIL))
        students = [db.scalar(select(User).where(User.email == e)) for e in STUDENT_EMAILS]
        classroom = db.get(Classroom, classroom.id)
        existing = db.scalar(select(Assignment).where(Assignment.classroom_id == classroom.id).order_by(Assignment.id))
        from pathlib import Path
        source = Path(json.loads(existing.dataset_json)[0]["path"])
        frame = pd.read_csv(source)
        assignment, questions, _, _, _ = add_assignment(db, classroom, TITLE, source, closed=True)
        assignment.description = "[DỮ LIỆU MẪU] Cùng một CSV, năm hướng phân tích: tổng hợp số liệu, tỷ suất lợi nhuận, tỷ trọng, lập luận thiếu bằng chứng và giới hạn về cơ cấu sản phẩm. Mở chia sẻ, đánh giá chéo, AI so sánh và nộp bản cải thiện."
        submissions = []
        for index, student in enumerate(students):
            answers, region = report_answers(frame, index)
            series = region["Biên lợi nhuận (%)"] if index == 1 else region["Tỷ trọng (%)"] if index == 2 else region["revenue"]
            title = "Bien loi nhuan theo vung (%)" if index == 1 else "Ty trong doanh thu (%)" if index == 2 else "Doanh thu theo vung (VND)"
            submission, versions = add_submission(db, assignment, questions, answers, series, title, student, index,
                                                  improved=index == 0, graded=index < 3, partial_answer=False)
            submissions.append((submission, versions))
            if index == 2:
                artifact = db.scalar(select(Artifact).join(AIJob).where(AIJob.assignment_id == assignment.id, AIJob.owner_id == student.id))
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.pie(series, labels=series.index, autopct="%1.1f%%", colors=["#308d75", "#8ac2a7", "#d4e7d9"])
                ax.set_title(title); fig.tight_layout(); fig.savefig(artifact.local_path, dpi=120); plt.close(fig)
            db.add(PeerReview(version_id=versions[0].id, reviewer_id=students[(index + 1) % 5].id,
                              rating=3 if index == 3 else 5,
                              strengths=f"[Mẫu] Tôi học được góc nhìn {STYLES[index]}.",
                              suggestions="Bổ sung công thức, đơn vị và giới hạn để người đọc kiểm chứng.",
                              learned="Phân biệt quy mô doanh thu, tỷ trọng và tỷ suất lợi nhuận."))
            db.add(Comment(submission_id=submission.id, author_id=students[(index + 2) % 5].id,
                           body="[Dữ liệu mẫu] Vì mỗi vùng gắn với một loại sản phẩm, mình nên kiểm tra thêm ảnh hưởng của đơn giá trước khi kết luận về địa lý."))
        db.flush()
        sample_job_ids = []
        for index, owner in enumerate([*students, teacher]):
            base_index = index if index < 5 else 0
            peer_indexes = [(base_index + 1) % 5, (base_index + 4) % 5]
            context = build_comparison_context(db, assignment, owner,
                deadline_version(db, assignment, submissions[base_index][0].id).id,
                [deadline_version(db, assignment, submissions[p][0].id).id for p in peer_indexes])
            context["demo"] = True
            for report in [context["base"], *context["peers"]]:
                report_index = next(i for i, s in enumerate(students) if s.id == report["student_id"])
                report["style"] = STYLES[report_index]; report["email"] = students[report_index].email
            result = sample_comparison(context)
            job = AIJob(owner_id=owner.id, assignment_id=assignment.id, version_id=context["base"]["version_id"],
                        kind="peer_comparison", status="done", prompt=json.dumps(context, ensure_ascii=False),
                        result_json=json.dumps(result, ensure_ascii=False))
            db.add(job); db.flush(); sample_job_ids.append(job.id)
        manifest = {"class_id": classroom.id, "assignment_id": assignment.id,
                    "comparison_job_ids": sample_job_ids, "created_at": utcnow().isoformat()}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return manifest


if __name__ == "__main__":
    main()

"""Optional local browser smoke test using isolated data and deterministic AI.

Run from backend: .venv/Scripts/python.exe tests/ui_learning_smoke.py
Build the frontend first. No real accounts, datasets or LLM calls are used.
"""
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conftest  # Isolate database and file storage before importing the app.
from test_peer_comparison import prepare
from test_peer_learning import submit
from app.database import SessionLocal
from app.main import app
from app.models import AIJob
from app import worker
from app.question_hints import IDEAS
from sqlalchemy import select
import uvicorn
from playwright.sync_api import sync_playwright, expect


def comparison(context):
    return {"mode": context["mode"], "summary": "Đã đối chiếu cách lập luận giữa các bài.",
        "next_steps": ["Tự kiểm tra bằng chứng và đơn vị."], "note": "Phản hồi giả lập để kiểm tra giao diện.",
        "sources": {"base": context["base"], "peers": context["peers"]}, "question_labels": context["questions"],
        "questions": [{"question_id": q["id"], "base_strengths": "Có nêu cách tiếp cận.", "base_gaps": "Cần làm rõ bằng chứng.",
            "peers": [{"version_id": p["version_id"], "similarities": "Cùng mục tiêu phân tích.", "differences": "Có thay đổi cách trình bày.", "learn_from_peer": "Kiểm tra thêm giới hạn."} for p in context["peers"]]} for q in context["questions"]]}


def hints(context):
    return {"question_id": context["question_id"], "ideas": [
        {"id": key, "title": IDEAS[key][0], "hint": IDEAS[key][1]} for key in ("scope", "chart", "limits")], "artifacts": []}


def check_account_ui(page):
    """Exercise both roles through the real registration form in test storage."""
    page.goto("http://127.0.0.1:4189/login")
    expect(page.get_by_role("form", name="Đăng nhập tài khoản")).to_be_visible()
    page.screenshot(path=str(conftest.TEST_DIR / "auth-login-desktop.png"), full_page=True)
    for role, label in (("student", "Sinh viên"), ("teacher", "Giáo viên")):
        page.get_by_role("button", name="Chuyển sang đăng ký", exact=True).click()
        page.get_by_label("Họ và tên", exact=True).fill(f"{label} Kiểm thử")
        page.get_by_label("Email", exact=True).fill(f"ui-{role}@test.local")
        page.get_by_label("Mật khẩu", exact=True).fill("short")
        page.get_by_role("button", name="Tạo tài khoản", exact=True).click()
        assert not page.get_by_label("Mật khẩu", exact=True).evaluate("el => el.validity.valid")
        page.get_by_label("Mật khẩu", exact=True).fill("UiPassword@2026")
        page.get_by_role("button", name="Hiện mật khẩu", exact=True).click()
        expect(page.get_by_label("Mật khẩu", exact=True)).to_have_attribute("type", "text")
        page.get_by_role("button", name="Ẩn mật khẩu", exact=True).click()
        page.locator(".auth-role-options label").filter(has_text=label).click()
        expect(page.get_by_role("radio", name=label, exact=True)).to_be_checked()
        page.screenshot(path=str(conftest.TEST_DIR / f"auth-register-{role}-desktop.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Registration overflow"
        page.screenshot(path=str(conftest.TEST_DIR / f"auth-register-{role}-mobile.png"), full_page=True)
        page.get_by_role("button", name="Tạo tài khoản", exact=True).click()
        expect(page.locator(".profile-copy small")).to_have_text(label)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Dashboard overflow"
        page.locator(".profile-button").click()
        expect(page.get_by_role("form", name="Đăng nhập tài khoản")).to_be_visible()
        page.screenshot(path=str(conftest.TEST_DIR / "auth-login-mobile.png"), full_page=True)
        page.set_viewport_size({"width": 1440, "height": 1000})
    page.get_by_label("Email", exact=True).fill("ui-student@test.local")
    page.get_by_label("Mật khẩu", exact=True).fill("IncorrectPassword")
    page.get_by_role("button", name="Đăng nhập", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Email hoặc mật khẩu chưa đúng")
    page.get_by_label("Mật khẩu", exact=True).fill("UiPassword@2026")
    page.get_by_role("button", name="Đăng nhập", exact=True).click()
    expect(page.locator(".profile-copy small")).to_have_text("Sinh viên")
    page.locator(".profile-button").click()


def capture_demo(browser):
    """Render realistic existing demo fixtures, still in the isolated database."""
    from app import seed_demo, seed_comparison_demo
    from app.models import Submission, SubmissionVote, User
    seed_demo.BASE_DIR = conftest.TEST_DIR
    seed_demo.main()
    manifest = seed_comparison_demo.main()
    with SessionLocal.begin() as db:
        students = list(db.scalars(select(User).where(User.email.in_(seed_demo.STUDENT_EMAILS)).order_by(User.id)))
        target = db.scalar(select(Submission).where(Submission.assignment_id == manifest["assignment_id"], Submission.student_id == students[1].id))
        for student in [students[0], students[2], students[3]]:
            db.add(SubmissionVote(submission_id=target.id, voter_id=student.id))
    page = browser.new_page(viewport={"width": 1440, "height": 1100})
    page.goto("http://127.0.0.1:4189")
    page.get_by_label("Email").fill(seed_demo.STUDENT_EMAILS[0])
    page.get_by_label("Mật khẩu", exact=True).fill(seed_demo.PASSWORD)
    page.get_by_role("button", name="Đăng nhập", exact=True).click()
    expect(page.get_by_role("navigation").get_by_role("link", name="Thảo luận", exact=True)).to_be_visible()
    page.screenshot(path=str(conftest.TEST_DIR / "theme-dashboard-desktop.png"), full_page=True)
    page.goto("http://127.0.0.1:4189/classes")
    expect(page.get_by_role("heading", name="Lớp học", exact=True)).to_be_visible()
    page.screenshot(path=str(conftest.TEST_DIR / "theme-classes-desktop.png"), full_page=True)
    page.get_by_role("button", name="Tham gia lớp", exact=True).click()
    expect(page.locator(".modal-card")).to_be_visible()
    page.screenshot(path=str(conftest.TEST_DIR / "theme-class-modal.png"), full_page=True)
    page.get_by_role("button", name="Đóng", exact=True).click()
    page.goto(f"http://127.0.0.1:4189/classes/{manifest['class_id']}")
    expect(page.locator(".class-hero h1")).to_be_visible()
    page.screenshot(path=str(conftest.TEST_DIR / "theme-class-detail.png"), full_page=True)
    page.goto(f"http://127.0.0.1:4189/assignments/{manifest['assignment_id']}")
    expect(page.locator(".workspace-title")).to_be_visible()
    assert "Segoe UI" in page.evaluate("getComputedStyle(document.body).fontFamily")
    page.screenshot(path=str(conftest.TEST_DIR / "theme-student-assignment.png"), full_page=True)
    suffix = f"?class={manifest['class_id']}&assignment={manifest['assignment_id']}"
    page.goto("http://127.0.0.1:4189/discussion" + suffix)
    expect(page.locator(".discussion-list-item")).to_have_count(5)
    expect(page.locator(".discussion-chart-preview img")).to_be_visible()
    page.screenshot(path=str(conftest.TEST_DIR / "community-discussion-desktop.png"), full_page=True)
    page.get_by_role("button", name="Xem toàn bộ bài làm", exact=True).click()
    expect(page.locator(".gallery-prose")).to_have_class("prose gallery-prose is-expanded")
    page.get_by_role("button", name="Thu gọn bài làm", exact=True).click()
    page.get_by_label("Tìm bài nộp").fill("Lê Thu Chi")
    expect(page.locator(".discussion-list-item")).to_have_count(1)
    page.locator(".discussion-list-item").click()
    expect(page.locator(".discussion-author-header")).to_contain_text("Lê Thu Chi")
    page.get_by_label("Tìm bài nộp").fill("khong-co-sinh-vien-nay")
    expect(page.get_by_text("Không tìm thấy bài nộp", exact=True)).to_be_visible()
    page.get_by_label("Tìm bài nộp").fill("")
    expect(page.locator(".discussion-list-item")).to_have_count(5)
    page.goto("http://127.0.0.1:4189/comparison" + suffix)
    expect(page.locator(".comparison-student-table tbody tr")).to_have_count(4)
    page.get_by_label("Tìm sinh viên để so sánh").fill("Trần Quốc Bảo")
    expect(page.locator(".comparison-student-table tbody tr")).to_have_count(1)
    page.get_by_role("button", name="Chọn tất cả", exact=True).click()
    expect(page.get_by_role("checkbox", name="Chọn bài của Trần Quốc Bảo (Demo)", exact=True)).to_be_checked()
    page.get_by_label("Tìm sinh viên để so sánh").fill("")
    page.get_by_label("Lịch sử so sánh").select_option(str(manifest["comparison_job_ids"][0]))
    expect(page.get_by_role("heading", name="Kết quả so sánh", exact=True)).to_be_visible()
    page.screenshot(path=str(conftest.TEST_DIR / "community-comparison-desktop.png"), full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile comparison overflow"
    assert not page.locator(".sidebar .side-label").is_visible(), "Sidebar heading must be hidden on mobile"
    page.screenshot(path=str(conftest.TEST_DIR / "community-comparison-mobile.png"), full_page=True)
    page.evaluate("window.scrollTo(0, 0)")
    page.screenshot(path=str(conftest.TEST_DIR / "community-comparison-mobile-top.png"))
    page.goto("http://127.0.0.1:4189/discussion" + suffix)
    expect(page.locator(".discussion-chart-preview img")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile discussion overflow"
    page.screenshot(path=str(conftest.TEST_DIR / "community-discussion-mobile.png"), full_page=True)
    page.evaluate("window.scrollTo(0, 0)")
    page.screenshot(path=str(conftest.TEST_DIR / "community-discussion-mobile-top.png"))
    page.close()
    teacher = browser.new_page(viewport={"width": 1440, "height": 1000})
    teacher.goto("http://127.0.0.1:4189/login")
    teacher.get_by_label("Email").fill(seed_demo.TEACHER_EMAIL)
    teacher.get_by_label("Mật khẩu", exact=True).fill(seed_demo.PASSWORD)
    teacher.get_by_role("button", name="Đăng nhập", exact=True).click()
    expect(teacher.locator(".profile-copy small")).to_have_text("Giáo viên")
    teacher.goto(f"http://127.0.0.1:4189/assignments/{manifest['assignment_id']}")
    expect(teacher.locator(".teacher-assignment-grid")).to_be_visible()
    teacher.screenshot(path=str(conftest.TEST_DIR / "theme-teacher-assignment.png"), full_page=True)
    teacher.locator(".student-submission").first.click()
    expect(teacher.locator(".modal-card")).to_be_visible()
    teacher.screenshot(path=str(conftest.TEST_DIR / "theme-grading-modal.png"), full_page=True)
    teacher.locator(".modal-close").click()
    teacher.goto(f"http://127.0.0.1:4189/classes/{manifest['class_id']}")
    teacher.get_by_role("button", name="Tạo bài tập", exact=True).click()
    expect(teacher.locator(".create-form")).to_be_visible()
    teacher.screenshot(path=str(conftest.TEST_DIR / "theme-create-assignment.png"), full_page=True)
    teacher.set_viewport_size({"width": 390, "height": 844})
    assert teacher.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Teacher form overflow"
    teacher.screenshot(path=str(conftest.TEST_DIR / "theme-create-assignment-mobile.png"), full_page=True)
    teacher.close()


def main():
    logging.getLogger("httpx").setLevel(logging.WARNING)
    cid, aid, original, other = prepare()
    improved = submit(aid, text="Bản cải thiện để kiểm tra giao diện")
    worker.compare_reports = comparison
    worker.question_hints = hints
    stop = threading.Event()

    def run_ai():
        while not stop.wait(.15):
            with SessionLocal() as db:
                ids = list(db.scalars(select(AIJob.id).where(AIJob.status == "queued", AIJob.kind.in_(["peer_comparison", "question_hint"])) ))
            for job_id in ids:
                worker._execute(job_id)

    api = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8009, log_level="error"))
    threading.Thread(target=api.run, daemon=True).start()
    threading.Thread(target=run_ai, daemon=True).start()
    frontend = Path(__file__).resolve().parents[2] / "frontend"
    env = {**os.environ, "WEB02_API_TARGET": "http://127.0.0.1:8009"}
    log = open(conftest.TEST_DIR / "vite.log", "w", encoding="utf-8")
    proc = subprocess.Popen(["node", str(frontend / "node_modules/vite/bin/vite.js"), "preview", "--host", "127.0.0.1", "--port", "4189", "--strictPort"],
        cwd=frontend, env=env, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    try:
        for _ in range(100):
            try:
                urlopen("http://127.0.0.1:4189", timeout=1)
                break
            except OSError:
                if proc.poll() is not None:
                    raise RuntimeError((conftest.TEST_DIR / "vite.log").read_text(encoding="utf-8"))
                time.sleep(.2)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            check_account_ui(page)
            page.goto("http://127.0.0.1:4189")
            page.get_by_label("Email").fill("student@test.edu")
            page.get_by_label("Mật khẩu", exact=True).fill("password123")
            page.get_by_role("button", name="Đăng nhập", exact=True).click()
            page.get_by_role("navigation").get_by_role("link", name="AI so sánh bài").click()
            expect(page.get_by_role("heading", name="AI so sánh bài", exact=True).first).to_be_visible()
            expect(page.get_by_label("Bài làm gốc")).to_have_value(str(original["version_id"]))
            expect(page.locator(".comparison-peer select")).to_have_count(0)
            page.get_by_role("button", name="Chọn tất cả", exact=True).click()
            page.get_by_role("button", name="Bắt đầu so sánh", exact=True).click()
            expect(page.get_by_text("Đã đối chiếu cách lập luận giữa các bài.")).to_be_visible(timeout=15000)
            page.get_by_role("button", name="So sánh 2 phiên bản của mình", exact=True).click()
            page.get_by_label("Phiên bản mới nộp lại").select_option(str(improved["version_id"]))
            page.get_by_role("button", name="Bắt đầu so sánh", exact=True).click()
            page.get_by_role("navigation", name="Kết quả theo câu hỏi").get_by_role("button", name="Câu hỏi 1", exact=True).click()
            expect(page.get_by_text("Bản mới nộp lại của tôi").first).to_be_visible(timeout=15000)
            page.screenshot(path=str(conftest.TEST_DIR / "comparison.png"), full_page=True)

            page.get_by_role("navigation").get_by_role("link", name="Thảo luận", exact=True).click()
            expect(page.get_by_role("heading", name="Thảo luận", exact=True)).to_be_visible()
            expect(page.locator(".ai-comparison")).to_have_count(0)
            card = page.locator(".gallery-card").filter(has=page.get_by_text("Other Student", exact=True))
            card.get_by_role("button", name="Bài hay").click()
            expect(card.get_by_role("button", name="Đã bình chọn · 1")).to_be_visible()
            card.get_by_label("Bình luận bài của Other Student").fill("Mình thích cách trình bày, bạn có thể bổ sung giới hạn.")
            card.get_by_role("button", name="Gửi bình luận").click()
            expect(card.get_by_text("Mình thích cách trình bày, bạn có thể bổ sung giới hạn.")).to_be_visible()
            card.get_by_text("Đánh giá phiên bản 1 và ghi điều học được", exact=True).click()
            card.get_by_label("Điểm tốt trong bài").fill("Cách trình bày rõ ràng.")
            card.get_by_label("Gợi ý để bài tốt hơn").fill("Bổ sung giới hạn dữ liệu.")
            card.get_by_label("Tôi học được gì từ bài này?").fill("Cách phân nhóm để kiểm tra.")
            card.get_by_role("button", name="Lưu đánh giá chéo").click()
            card.get_by_role("button", name="Thảo luận 1", exact=True).click()
            expect(card.get_by_text("Cách trình bày rõ ràng.", exact=True)).to_be_visible()
            page.screenshot(path=str(conftest.TEST_DIR / "discussion.png"), full_page=True)

            page.goto(f"http://127.0.0.1:4189/assignments/{aid}")
            page.get_by_role("button", name="Gợi ý ý tưởng", exact=True).click()
            expect(page.get_by_text(IDEAS["chart"][1], exact=True)).to_be_visible(timeout=15000)
            page.screenshot(path=str(conftest.TEST_DIR / "hints.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(f"http://127.0.0.1:4189/comparison?class={cid}&assignment={aid}")
            expect(page.get_by_role("button", name="So sánh 2 phiên bản của mình", exact=True)).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile overflow"
            page.screenshot(path=str(conftest.TEST_DIR / "comparison-mobile.png"), full_page=True)
            assert not errors, errors
            if "--visual" in sys.argv:
                capture_demo(browser)
            browser.close()
        checks = ["student and teacher registration", "login and invalid credentials", "password visibility", "peer comparison", "self comparison", "votes", "comments", "peer reviews", "question hints", "mobile layout"]
        if "--visual" in sys.argv:
            checks += ["dashboard and classes", "class dialog", "teacher assignment", "grading dialog", "assignment creation"]
        print(json.dumps({"status": "passed", "checks": checks, "artifacts": str(conftest.TEST_DIR)}, ensure_ascii=False))
    finally:
        stop.set()
        api.should_exit = True
        proc.terminate()
        proc.wait(timeout=15)
        log.close()


if __name__ == "__main__":
    main()

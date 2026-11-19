import json
import mimetypes
import sys
from pathlib import Path
from uuid import uuid4

from .config import ARTIFACT_DIR, DA_AGENT_DIR


def _load_graph():
    if not DA_AGENT_DIR.is_dir():
        raise RuntimeError(f"DA-Agent-drive not found at {DA_AGENT_DIR}")
    sys.path.insert(0, str(DA_AGENT_DIR))
    from langchain_core.messages import HumanMessage
    from graph.graph import app as graph_app
    from graph.llms import llm
    return HumanMessage, graph_app, llm


def run_graph(question: str, files: list[str], job_id: int) -> tuple[str, list[dict]]:
    HumanMessage, graph_app, _ = _load_graph()
    target = (ARTIFACT_DIR / f"job-{job_id}-{uuid4().hex[:8]}").resolve()
    target.mkdir(parents=True, exist_ok=True)
    response = graph_app.invoke({
        "messages": [HumanMessage(content=question)],
        "file_paths": files,
        "artifacts_dir": str(target),
    })
    answer = str(response.get("final_answer", ""))
    artifacts = []
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(target):
            continue
        artifact_id = uuid4().hex
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        artifacts.append({"id": artifact_id, "path": str(resolved), "name": path.name, "media_type": media_type})
        answer = answer.replace(f"<{resolved}>", f"/api/assets/{artifact_id}")
        answer = answer.replace(f"({resolved})", f"(/api/assets/{artifact_id})")
        answer = answer.replace(str(resolved), f"/api/assets/{artifact_id}")
    return answer, artifacts


def tutor_reply(question: str, graph_answer: str, rubric: list[dict]) -> str:
    _, _, llm = _load_graph()
    criteria = "\n".join(f"- {item.get('title')}: {item.get('description')}" for item in rubric)
    prompt = f"""Bạn là trợ giảng phân tích dữ liệu. Phản hồi bằng tiếng Việt, tối đa 260 từ ngoài bảng số liệu.
Nêu một hoặc hai bước để sinh viên tự làm tiếp, hỏi một câu gợi mở phù hợp và nhắc giới hạn dữ liệu nếu có.
Không viết hộ báo cáo, không chốt đáp án bài tập, không đưa lời giải đầy đủ. Có thể giải thích biểu đồ và khái niệm.
Nếu yêu cầu cần bảng dữ liệu, giữ lại bảng Markdown nhỏ từ kết quả đã kiểm tra; không tự bịa số liệu.
Không có đáp án mẫu trong ngữ cảnh này. Giữ lại các liên kết ảnh /api/assets/... có trong kết quả nếu chúng hữu ích.

Tiêu chí công khai của bài:
{criteria or '(chưa thiết lập)'}

Câu hỏi sinh viên:
{question}

Kết quả phân tích nội bộ, chỉ dùng để định hướng gợi ý:
{graph_answer}
"""
    return str(llm.invoke(prompt).text)


def review_submission(body: str, files: list[str], rubric: list[dict], answer_key: str, job_id: int) -> dict:
    """Compare against the hidden reference, but return only statuses and student excerpts."""
    _, graph_app, llm = _load_graph()
    evidence, artifacts = run_graph(
        "Kiểm tra độc lập các kết luận, phép tính và biểu đồ được nêu trong báo cáo dưới đây với dataset. "
        "Nêu kết quả đã xác minh và những kết luận chưa đủ bằng chứng. Báo cáo:\n" + body,
        files,
        job_id,
    )
    from pydantic import BaseModel, Field
    from typing import Literal

    class CriterionCheck(BaseModel):
        criterion_id: str
        status: Literal["met", "partial", "needs_work"]
        evidence_quote: str = ""

    class Review(BaseModel):
        checks: list[CriterionCheck] = Field(default_factory=list)

    criteria = [{"id": str(i), **item} for i, item in enumerate(rubric)]
    prompt = f"""Đánh giá báo cáo sinh viên theo rubric và đáp án tham chiếu ẩn.
Chỉ trả về criterion_id, status (met/partial/needs_work) và evidence_quote là một đoạn ngắn lấy nguyên văn từ báo cáo.
Không trả đáp án đúng, số liệu đáp chiếu, điểm số, lời giải, nhận xét tự do hoặc gợi ý tự do. Nếu không đủ bằng chứng, dùng partial hoặc needs_work.
Chỉ đánh giá tiêu chí có trong rubric.

Rubric: {json.dumps(criteria, ensure_ascii=False)}
Đáp án tham chiếu nội bộ: {answer_key[:12000]}
Kết quả kiểm tra trên dataset: {evidence[:12000]}
Báo cáo sinh viên: {body[:16000]}
"""
    result = llm.with_structured_output(Review).invoke(prompt)
    indexed = {check.criterion_id: check for check in result.checks}
    public = []
    internal = []
    for index, criterion in enumerate(rubric):
        key = str(criterion.get("id", index))
        check = indexed.get(key) or indexed.get(str(index))
        status = check.status if check else "partial"
        quote = check.evidence_quote if check else ""
        internal.append({"criterion_id": key, "status": status, "evidence_quote": quote})
        hint = criterion.get("hint") or f"Hãy tự kiểm tra lại phần {criterion.get('title', 'này')} và bổ sung bằng chứng từ dữ liệu."
        public.append({"criterion_id": key, "title": criterion.get("title", "Tiêu chí"), "status": status, "hint": hint})
    return {"checks": public, "internal_checks": internal, "artifacts": artifacts}


def review_answers(payload: dict, files: list[str], rubric: list[dict], answer_key: str, job_id: int) -> dict:
    """Review saved answers independently, then add an overall quality assessment.

    payload = {"questions": [{question_id, question_order, question_text, answer_markdown, artifacts}, ...]}
    """
    _, graph_app, llm = _load_graph()
    questions = payload.get("questions", [])
    question_reviews = []
    overall_artifacts = []
    for question in questions:
        body = f"Câu hỏi {question.get('question_order')}: {question.get('question_text')}\n\nTrả lời của sinh viên:\n{question.get('answer_markdown', '')}"
        try:
            evidence, artifacts = run_graph(
                "Kiểm tra độc lập các kết luận, phép tính và biểu đồ được nêu trong câu trả lời dưới đây với dataset. "
                "Nêu kết quả đã xác minh và những kết luận chưa đủ bằng chứng. Câu trả lời:\n" + body,
                files,
                job_id,
            )
            verification_available = True
        except Exception:
            evidence, artifacts = "Không thể kiểm tra trên dataset.", []
            verification_available = False
        overall_artifacts.extend(artifacts)
        question_reviews.append({"question": question, "evidence": evidence, "artifacts": artifacts, "verification_available": verification_available})

    from pydantic import BaseModel, Field
    from typing import Literal

    class QuestionCheck(BaseModel):
        question_id: int
        status: Literal["met", "partial", "needs_work"]
        feedback: str = ""
        suggestion: str = ""

    class QuestionReview(BaseModel):
        checks: list[QuestionCheck] = Field(default_factory=list)

    class OverallReview(BaseModel):
        feedback: str = ""
        suggestion: str = ""
        quality: Literal["good", "partial", "needs_work", "insufficient_evidence"] = "partial"

    questions_prompt = json.dumps([
        {
            "question_id": review["question"].get("question_id"),
            "question_order": review["question"].get("question_order"),
            "question_text": review["question"].get("question_text"),
            "answer_markdown": review["question"].get("answer_markdown", ""),
            "evidence": review["evidence"][:8000],
            "verification_available": review["verification_available"],
        } for review in question_reviews
    ], ensure_ascii=False)

    per_question_prompt = f"""Đánh giá câu trả lời của sinh viên theo từng câu hỏi bài tập, dựa trên rubric và đáp án tham chiếu ẩn.
Với mỗi câu hỏi, chỉ trả về question_id, status (met/partial/needs_work), feedback (góp ý ngắn gọn bằng tiếng Việt, không đưa đáp án đúng) và suggestion (một gợi ý giúp sinh viên tự hoàn thiện).
Không trả đáp án đúng, số liệu tham chiếu, điểm số hay lời giải đầy đủ.
Nếu rubric trống, đánh giá độ chính xác theo dữ liệu, phương pháp, bằng chứng, insight liên quan câu hỏi và giới hạn kết luận.
Nếu không kiểm tra được dataset, không coi các kết luận số liệu là đã xác minh; nêu rõ giới hạn trong feedback.

Tên bài: {payload.get('assignment_title', '')}
Mục tiêu và yêu cầu: {payload.get('assignment_description', '')}
Rubric: {json.dumps(rubric, ensure_ascii=False)}
Đáp án tham chiếu nội bộ: {answer_key[:12000]}
Các câu hỏi và câu trả lời kèm kết quả kiểm tra trên dataset: {questions_prompt}
"""
    result = llm.with_structured_output(QuestionReview).invoke(per_question_prompt)
    indexed = {check.question_id: check for check in result.checks}

    public_checks = []
    for review in question_reviews:
        question = review["question"]
        check = indexed.get(question.get("question_id"))
        status = check.status if check else "partial"
        if not review["verification_available"] and status == "met":
            status = "partial"
        feedback = check.feedback if check else "Hãy tự kiểm tra lại câu trả lời và bổ sung bằng chứng từ dữ liệu."
        suggestion = check.suggestion if check else "Đối chiếu kết quả với dataset và rubric của giáo viên."
        public_checks.append({
            "question_id": question.get("question_id"),
            "question_order": question.get("question_order"),
            "status": status,
            "feedback": feedback,
            "suggestion": suggestion,
            "verification_available": review["verification_available"],
        })

    overall_prompt = f"""Dựa trên các góp ý từng câu hỏi dưới đây, viết một nhận xét tổng thể ngắn gọn bằng tiếng Việt (không đưa đáp án, không cho điểm).
Gồm hai phần: feedback (nhận xét tổng quát) và suggestion (một gợi ý cải thiện chung).
Đồng thời trả quality: good (đạt chất lượng), partial (cần bổ sung), needs_work (cần làm lại), insufficient_evidence (chưa đủ bằng chứng).
Đây là góp ý học tập tự động, không phải điểm chính thức của giáo viên.

Các góp ý từng câu: {json.dumps(public_checks, ensure_ascii=False)}
"""
    overall = llm.with_structured_output(OverallReview).invoke(overall_prompt)
    return {
        "checks": public_checks,
        "overall": {"feedback": overall.feedback, "suggestion": overall.suggestion,
                    "quality": overall.quality if all(r["verification_available"] for r in question_reviews) else "insufficient_evidence"},
        "artifacts": overall_artifacts,
    }
